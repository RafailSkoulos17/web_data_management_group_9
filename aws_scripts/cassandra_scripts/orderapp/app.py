from cassandra.cluster import Cluster
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
cluster = Cluster(['34.228.27.238'])
session = cluster.connect()
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS orderspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['34.228.27.238'], "cqlengine", protocol_version=3)
sync_table(Order)

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
    users = requests.get("http://3.217.184.15:8080/users/find/"+user_id)
    users = json.loads(users.text)
    if len(users) == 0:
        return response({"message": "User id is not valid"}, False)
    else:
        order_id = uuid.uuid4()
        if "product" not in data:
            data["product"] = {}
        data["product"] = {uuid.UUID(k): v for k, v in data["product"].items()}
        order = Order.create(first_name=users["first_name"], last_name=users["last_name"], product=data["product"],
                             user_id=uuid.UUID(user_id), order_id=order_id, payment_status=False)
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
        current_product = Order.objects(order_id=order_id).if_exists().get().get_data()["product"]
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    if item_id in current_product:
        current_product[item_id] += 1
    else:
        current_product[item_id] = 1
    try:
        Order.objects(order_id=order_id).if_exists().update(product=current_product)
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    except LWTException:
        return response({"message": "Order or item not found"}, False)
    return response(Order.objects(order_id=order_id).if_exists().get().get_data(), True)


@app.route("/orders/removeItem/<uuid:order_id>/<uuid:item_id>", methods=["DELETE"])
@json_api
def remove_item(order_id, item_id):
    try:
        current_product = Order.objects(order_id=order_id).if_exists().get().get_data()["product"]
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    try:
        if item_id in current_product:
            if current_product[item_id] > 1:
                current_product[item_id] -= 1
                Order.objects(order_id=order_id).if_exists().update(product__update=current_product)
            else:
                Order.objects(order_id=order_id).if_exists().update(product__remove={item_id})
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
        'http://3.217.184.15:8082/payment/pay/{0}/{1}'.format(current_order['user_id'], current_order['order_id']))

    if not pay_response.json()['success']:
        return response({"message": "Something went wrong with the payment"}, False)

    prods_subtracted = {}
    products = current_order["product"]
    for prod, num in products.items():
        sub_response = requests.post(
            'http://3.217.184.15:8083/stock/subtract/{0}/{1}'.format(prod, num))
        if not sub_response.json()['success']:
            pay_response = requests.post(
                'http://3.217.184.15:8082/payment/cancelPayment/{0}/{1}'.format(current_order['user_id'], current_order['order_id']))

            for sub_prod, sub_num in prods_subtracted.items():
                sub_response = requests.post(
                    'http://3.217.184.15:8083/stock/add/{0}/{1}'.format(sub_prod, sub_num))

            return response({'message': 'Stock has not {0} {1}(s) available'.format(num, prod)}, False)
        else:
            prods_subtracted[prod] = num

    Order.objects(order_id=order_id).if_exists().update(payment_status__update=True)
    return response({'message': 'Checkout was completed successfully'}, True)
