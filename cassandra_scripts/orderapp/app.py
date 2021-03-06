from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from flask import Flask, jsonify
from flask import Response
from models.order import Order
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
import util
from functools import wraps
import json
from json import JSONDecodeError
import flask
from cassandra.cqlengine.query import LWTException, DoesNotExist
from util import response
import uuid
import requests

# establish the Flask app
app = Flask(__name__)
app.debug = True  # for testing reasons
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')  # authorization provider
cluster = Cluster(['3.18.214.57', '3.14.6.247', '18.223.205.111'], protocol_version=2, auth_provider=auth_provider)
session = cluster.connect()  # connect to the Cassandra cluster
# session.execute("DROP KEYSPACE IF EXISTS orderspace;")  # for testing reasons
# and create the keyspace if not existing
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS orderspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['3.18.214.57', '3.14.6.247', '18.223.205.111'], "cqlengine", protocol_version=2, auth_provider=auth_provider)
sync_table(Order)

user_ip = 'userLB-1223433602.us-east-2.elb.amazonaws.com'
payment_ip = 'paymentLB-1173775124.us-east-2.elb.amazonaws.com'
stock_ip = 'stockLB-369039842.us-east-2.elb.amazonaws.com'


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@app.route("/")
def home():
    return jsonify(result={"status": 200})  # 'Welcome to Orders API :)'


@app.route("/orders/create/<uuid:user_id>", methods=["POST"])
@json_api
# Functionality for creating an order
def create_order(user_id):
    data = json.loads((flask.request.data).decode('utf-8'))
    user_id = str(user_id)
    try:
        # check if the user exists
        users = requests.get("http://{0}/users/find/{1}".format(user_ip, user_id))
        if not users:
            return response({"message": "Something went wrong with retrieving the user"}, False)
        else:
            users = json.loads(users.text)
            if not users["success"]:
                return response({"message": "User id is not valid"}, False)
            else:
                amount = 0
                order_id = uuid.uuid4()
                if "product" not in data:
                    data["product"] = {}
                else:
                    # and obtain all the objects put in the "shopping cart"
                    for prod, am in data["product"].items():
                        product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip, str(prod)))
                        if not product:
                            return response({"message": "Something went wrong with the stock id"}, False)
                        product = json.loads(product.text)
                        amount += product["price"] * am
                    data["product"] = {uuid.UUID(k): v for k, v in data["product"].items()}
                order = Order.if_not_exists().create(first_name=users["first_name"], last_name=users["last_name"],
                                                     product=data["product"], user_id=uuid.UUID(user_id),
                                                     order_id=order_id, payment_status=False, amount=amount)
                order.save()
                return response(order.get_data(), True)
    except JSONDecodeError:
        return response({"message": "Something went wrong with json"}, False)
    except LWTException:
        return response({'message': 'Order already there'}, False)


@app.route("/orders/remove/<uuid:order_id>", methods=["DELETE"])
@json_api
# Functionality for deleting an order
def delete_order(order_id):
    try:
        Order.objects(order_id=order_id).if_exists().delete()
    except LWTException:
        return response({"message": "Order cannot be removed"}, False)
    return response({"message": "Order was removed"}, True)


@app.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
# Functionality for finding an order
def find_order(order_id):
    try:
        order = Order.objects(order_id=order_id).if_exists().get()
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    return response(order.get_data(), True)


@app.route("/orders/addItem/<uuid:order_id>/<uuid:item_id>", methods=["POST"])
@json_api
# Functionality for adding an item in the order
def add_item(order_id, item_id):
    try:
        current_order = Order.objects(order_id=order_id).if_exists().get().get_data()
        current_product = current_order["product"]
        current_amount = current_order["amount"]
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(item_id)))
    if not product:
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
# Functionality for removing an item from the order
def remove_item(order_id, item_id):
    try:
        current_order = Order.objects(order_id=order_id).if_exists().get().get_data()
        current_product = current_order["product"]
        current_amount = current_order["amount"]
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(item_id)))
    if not product:
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
# Functionality for checking out an order
def checkout(order_id):
    try:
        # check if the order exists
        current_order = Order.objects(order_id=order_id).if_exists().get().get_data()
    except DoesNotExist:
        return response({"message": "Order does not exist"}, False)
    # and if it is not already paid
    if current_order['payment_status']:
        return response({'message': 'Order already completed'}, False)
    try:
        # attempt to pay it
        pay_response = requests.post(
            'http://{0}/payment/pay/{1}/{2}'.format(payment_ip, current_order['user_id'], current_order['order_id']))

        if not pay_response:
            return response({"message": "Something went wrong with the payment -> probably down"}, False)
        else:
            pay_response = json.loads(pay_response.text)
            # in failure of having enough credits then abort
            if not pay_response['success']:
                return response({"message": "Something went wrong with the payment"}, False)
            else:
                prods_subtracted = {}
                products = current_order["product"]
                # subtract the stock amount for each product in the order
                for prod, num in products.items():
                    sub_response = requests.post(
                        'http://{0}/stock/subtract/{1}/{2}'.format(stock_ip, prod, num))
                    if not sub_response:
                        return response({"message": "Something went wrong when subtracting the stock"}, False)
                    else:
                        # if something is not in sufficient quantity cancel the payment
                        if not sub_response.json()['success']:
                            pay_response = requests.post(
                                'http://{0}/payment/cancelPayment/{1}/{2}'.format(payment_ip,current_order['user_id'],
                                                                                                current_order['order_id']))
                            if not pay_response:
                                return response({"message": "Something went wrong when cancelling the payment"}, False)
                            else:
                                # and increase again the quantity of the products subtracted so far in the order
                                for sub_prod, sub_num in prods_subtracted.items():
                                    sub_response = requests.post(
                                        'http://{0}/stock/add/{1}/{2}'.format(stock_ip, sub_prod, sub_num))
                                    if not sub_response:
                                        return response({"message": "Something went wrong when adding the stock"}, False)

                                return response({'message': 'Stock has not {0} {1}(s) available'.format(num, prod)}, False)
                        else:
                            prods_subtracted[prod] = num
                # if this point is reached the order has been checked out successfully
                Order.objects(order_id=order_id).if_exists().update(payment_status__update=True)
                return response({'message': 'Checkout was completed successfully'}, True)
    except JSONDecodeError:
        return response({"message": "Something went wrong with json in checkout"}, False)
