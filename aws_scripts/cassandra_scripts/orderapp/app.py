from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from flask import Flask
from flask import Blueprint, Response
from models.order import Order
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
import util
from functools import wraps
import json
import flask
from cassandra.cqlengine.query import LWTException, DoesNotExist
from util import response
import uuid
import requests

app = Flask(__name__)
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cluster = Cluster(['3.14.247.82','18.188.104.49','3.19.26.234'],protocol_version=2, auth_provider=auth_provider)
session = cluster.connect()
#session.execute("DROP KEYSPACE IF EXISTS orderspace;")
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS orderspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['3.14.247.82','18.188.104.49','3.19.26.234'], "cqlengine", protocol_version=2,auth_provider=auth_provider)
sync_table(Order)

user_ip = '18.191.23.53'
payment_ip = '18.223.161.135'
stock_ip = '18.216.96.248'


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@app.route("/")
def home():
    return 'Welcome to Orders API :)'


@app.route("/orders/create/<uuid:user_id>", methods=["POST"])
@json_api
def create_order(user_id):
    data = json.loads((flask.request.data).decode('utf-8'))
    user_id = str(user_id)
    users = requests.get("http://{0}/users/find/{1}".format(user_ip,user_id))
    if users is None:
        return response({"message": "Something went wrong with retrieving the user"}, False)
    else:
        users = json.loads(users.text)
        if len(users) == 0:
            return response({"message": "User id is not valid"}, False)
        else:
            amount = 0
            order_id = uuid.uuid4()
            if "product" not in data:
                data["product"] = {}
            else:
                for prod, am in data["product"].items():
                    product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(prod)))
                    if product is None:
                        return response({"message": "Something went wrong with the stock id"}, False)
                    product = json.loads(product.text)
                    amount += product["price"] * am
                data["product"] = {uuid.UUID(k): v for k, v in data["product"].items()}
            order = Order.create(first_name=users["first_name"], last_name=users["last_name"], product=data["product"],
                                 user_id=uuid.UUID(user_id), order_id=order_id, payment_status=False, amount=amount)
            order.save()
            return response(order.get_data(), True)


@app.route("/orders/remove/<uuid:order_id>", methods=["DELETE"])
@json_api
def delete_order(order_id):
    try:
        Order.objects(order_id=order_id).if_exists().delete()
    except LWTException:
        return response({"message": "Order cannot be removed"}, False)
    return response({"message": "Order was removed"}, True)


@app.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
def find_order(order_id):
    try:
        order = Order.objects(order_id=order_id).if_exists().get()
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    return response(order.get_data(), True)


@app.route("/orders/addItem/<uuid:order_id>/<uuid:item_id>", methods=["POST"])
@json_api
def add_item(order_id, item_id):
    try:
        current_order = Order.objects(order_id=order_id).if_exists().get().get_data()
        current_product = current_order["product"]
        current_amount = current_order["amount"]
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(item_id)))
    if product is None:
        return response({"message": "Something went wrong with retrieving the item"}, False)
    if item_id in current_product:
        current_product[item_id] += 1
    else:
        current_product[item_id] = 1
    product = json.loads(product.text)
    current_amount += product["price"]
    try:
        Order.objects(order_id=order_id).if_exists().update(product=current_product, amount=current_amount)
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    except LWTException:
        return response({"message": "Order or item not found"}, False)
    return response(Order.objects(order_id=order_id).if_exists().get().get_data(), True)


@app.route("/orders/removeItem/<uuid:order_id>/<uuid:item_id>", methods=["DELETE"])
@json_api
def remove_item(order_id, item_id):
    try:
        current_order = Order.objects(order_id=order_id).if_exists().get().get_data()
        current_product = current_order["product"]
        current_amount = current_order["amount"]
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(item_id)))
    if product is None:
        return response({"message": "Something went wrong when retrieving the item"}, False)
    try:
        if item_id in current_product:
            product = json.loads(product.text)
            current_amount -= product["price"]
            if current_product[item_id] > 1:
                current_product[item_id] -= 1
                Order.objects(order_id=order_id).if_exists().update(product__update=current_product,
                                                                    amount__update=current_amount)
            else:
                Order.objects(order_id=order_id).if_exists().update(product__remove={item_id},
                                                                    amount__update=current_amount)
        else:
            return response({"message": "The item given does not exist"}, False)
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    except LWTException:
        return response({"message": "Order or item not found"}, False)
    return response(Order.objects(order_id=order_id).if_exists().get().get_data(), True)


@app.route("/orders/checkout/<uuid:order_id>", methods=["POST"])
@json_api
def checkout(order_id):
    try:
        current_order = Order.objects(order_id=order_id).if_exists().get().get_data()
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    if current_order['payment_status']:
        return response({'message': 'Order already completed'}, False)
    pay_response = requests.post(
        'http://{0}/payment/pay/{1}/{2}'.format(payment_ip, current_order['user_id'], current_order['order_id']))

    if pay_response is None:
        return response({"message": "Something went wrong with the payment -> probably down"}, False)
    if not pay_response.json()['success']:
        return response({"message": "Something went wrong with the payment"}, False)

    prods_subtracted = {}
    products = current_order["product"]
    for prod, num in products.items():
        sub_response = requests.post(
            'http://{0}/stock/subtract/{1}/{2}'.format(stock_ip,prod, num))
        if sub_response is None:
            return response({"message": "Something went wrong when subtracting the stock"}, False)
        if not sub_response.json()['success']:
            pay_response = requests.post(
                'http://{0}/payment/cancelPayment/{1}/{2}'.format(payment_ip,current_order['user_id'],
                                                                                current_order['order_id']))
            if pay_response is None:
                return response({"message": "Something went wrong when cancelling the payment"}, False)

            for sub_prod, sub_num in prods_subtracted.items():
                sub_response = requests.post(
                    'http://{0}/stock/add/{1}/{2}'.format(stock_ip,sub_prod, sub_num))
                if sub_response is None:
                    return response({"message": "Something went wrong when adding the stock"}, False)

            return response({'message': 'Stock has not {0} {1}(s) available'.format(num, prod)}, False)
        else:
            prods_subtracted[prod] = num

    Order.objects(order_id=order_id).if_exists().update(payment_status__update=True)
    return response({'message': 'Checkout was completed successfully'}, True)
