from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
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
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cluster = Cluster(['3.14.247.82', '18.188.104.49', '3.19.26.234'],protocol_version=2, auth_provider=auth_provider)
session = cluster.connect()
#session.execute("DROP KEYSPACE IF EXISTS paymentspace;")
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS paymentspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['3.14.247.82', '18.188.104.49', '3.19.26.234'], "cqlengine", protocol_version=2,auth_provider=auth_provider)
sync_table(Payment)

user_ip = '18.191.23.53'
order_ip = '18.188.32.79'
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
    return 'Welcome to Payment API :)'


@app.route("/payment/pay/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def pay(user_id, order_id):
    users = requests.get("http://{0}/users/find/{1}".format(user_ip, str(user_id)))
    if users is None:
        return util.response({"message": "Something went wrong with retrieving the user"}, False)
    user = json.loads(users.text)
    orders = requests.get("http://{0}/orders/find/{1}".format(order_ip, str(order_id)))
    if orders is None:
        return util.response({"message": "Something went wrong with retrieving the order"}, False)
    order = json.loads(orders.text)
    if len(user) == 0 or len(order) == 0:
        return util.response({"message": "User id or Order id is not valid"}, False)
    else:
        if order["user_id"] == str(user_id):
            amount = order["amount"]
            subtract_response = requests.post(
                'http://{0}/users/credit/subtract/{1}/{2}'.format(user_ip, user_id, amount)) # to put the public ip
            if subtract_response is None:
                return util.response({"message": "Something went wrong when subtracting the credit"}, False)
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
                    'http://{0}/users/credit/add/{1}/{2}'.format(user_ip, payment['user_id'], amount)) # to put the public ip
                if add_response is None:
                    return util.response({"message": "Something went wong when adding credit to user"}, False)
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

