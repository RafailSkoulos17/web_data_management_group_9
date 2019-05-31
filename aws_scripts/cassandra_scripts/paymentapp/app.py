from cassandra.cluster import Cluster
from flask import Flask
from flask import Blueprint, Response
import util
from functools import wraps
import json
import flask
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from models.payment import Payment
from cassandra.cqlengine.query import LWTException, DoesNotExist
import uuid
import requests

app = Flask(__name__)
cluster = Cluster(['34.228.27.238'])
session = cluster.connect()
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS paymentspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['34.228.27.238'], "cqlengine", protocol_version=3)
sync_table(Payment)


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@app.route("/")
def home():
    return 'Welcome to Payment API :)'


@app.route("/payment/pay/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def pay(user_id, order_id):
    users = requests.get("http://3.217.184.15:8080/users/find/"+str(user_id))
    user = json.loads(users.text)
    orders = requests.get("http://3.217.184.15:8081/orders/find/"+str(order_id))
    order = json.loads(orders.text)
    if len(user) == 0 or len(order) == 0:
        return util.response({"message": "User id or Order id is not valid"}, False)
    else:
        if order["user_id"] == str(user_id):
            amount = sum([x for x in order["product"].values()])
            subtract_response = requests.post(
                'http://3.217.184.15:8080/users/credit/subtract/{0}/{1}'.format(user_id, amount))
            sub_response = subtract_response.json()['success']
            if not sub_response:
                return util.response({"message": "Not enough credits for the payment"}, False)
            else:
                payment = Payment.create(first_name=user["first_name"], last_name=user["last_name"], email=user["email"]
                                         , amount=amount, user_id=user_id
                                         , order_id=order["order_id"], payment_id=uuid.uuid4(), status=True)
                payment.save()
                return util.response({}, Payment.objects(order_id=order_id).if_exists().get().get_status())
        else:
            return util.response({"message": "Wrong order"+order["user_id"]}, False)


@app.route("/payment/cancelPayment/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def cancel_payment(user_id, order_id):
    payments = Payment.objects.filter(order_id=order_id)
    if len(payments.all()) != 1:
        return util.response({"message": "Cancellation is not valid"}, False)
    else:
        payment = payments.all()[0]
        if payment["user_id"] == str(user_id):
            amount = payment["amount"]
            if Payment.objects(order_id=order_id).get().get_status()['status']:
                add_response = requests.post(
                    'http://3.217.184.15:8080/users/credit/add/{0}/{1}'.format(payment['user_id'], amount))
                Payment.objects(order_id=order_id).update(status=False)
                return util.response(Payment.objects(order_id=order_id).get().get_data(), True)
            else:
                return util.response({"message": "The payment has already been canceled"}, False)
        else:
            return util.response({"message": "The user had never paid"}, False)


@app.route("/payment/status/<uuid:order_id>", methods=["GET"])
@json_api
def get_status(order_id):
    payments = Payment.objects.filter(order_id=order_id)
    if len(payments.all()) != 1:
        return util.response({"message": "get status is not valid"}, False)
    else:
        return util.response(Payment.objects(order_id=order_id).if_exists().get().get_status(), True)
