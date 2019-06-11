from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from flask import Flask, jsonify
from flask import Response
import util
from functools import wraps
import json
from json import JSONDecodeError
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from models.payment import Payment
from cassandra.cqlengine.query import LWTException, DoesNotExist
import uuid
import requests

# establish the Flask app
app = Flask(__name__)
app.debug = True  # for testing reasons
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')  # authorization provider
cluster = Cluster(['3.18.214.57', '3.14.6.247', '18.223.205.111'], protocol_version=2, auth_provider=auth_provider)
session = cluster.connect()
# session.execute("DROP KEYSPACE IF EXISTS paymentspace;")  # for testing reasons
# and create the keyspace if not existing
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS paymentspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['3.18.214.57', '3.14.6.247', '18.223.205.111'], "cqlengine", protocol_version=2, auth_provider=auth_provider)
sync_table(Payment)

# domain names of the endpoints of the load balancers handling the traffic for each service
user_ip = 'userLB-1223433602.us-east-2.elb.amazonaws.com'
order_ip = 'orderLB-1640292742.us-east-2.elb.amazonaws.com'
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
    return jsonify(result={"status": 200})  # 'Welcome to Payment API :)'


@app.route("/payment/pay/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
# Functionality for paying an order
def pay(user_id, order_id):
    try:
        # first check if the user exists
        users = requests.get("http://{0}/users/find/{1}".format(user_ip, str(user_id)))
        if not users:
            return util.response({"message": "Something went wrong with retrieving the user"}, False)
        else:
            user = json.loads(users.text)
            # then check if the order is valid
            orders = requests.get("http://{0}/orders/find/{1}".format(order_ip, str(order_id)))
            if not orders:
                return util.response({"message": "Something went wrong with retrieving the order"}, False)
            else:
                order = json.loads(orders.text)
                if not user["success"] or not order["success"]:
                    return util.response({"message": "User id or Order id is not valid"}, False)
                else:
                    if order["user_id"] == str(user_id):
                        # try to subtract the amount of the order from the user's credits
                        amount = order["amount"]
                        subtract_response = requests.post(
                            'http://{0}/users/credit/subtract/{1}/{2}'.format(user_ip, user_id, amount))
                        if not subtract_response:
                            return util.response({"message": "Something went wrong when subtracting the credit"}, False)
                        else:
                            sub_response = subtract_response.json()['success']
                            # if not enough credits then abort the payment
                            if not sub_response:
                                return util.response({"message": "Not enough credits for the payment"}, False)
                            else:
                                # else complete the payment
                                payment = Payment.if_not_exists().create(first_name=user["first_name"],
                                                                         last_name=user["last_name"],
                                                                         email=user["email"],
                                                                         amount=amount, user_id=user_id,
                                                                         order_id=order["order_id"],
                                                                         payment_id=uuid.uuid4(), status=True)
                                payment.save()
                                return util.response({}, Payment.objects(order_id=order_id).if_exists().get().get_status())
                    else:
                        return util.response({"message": "Wrong order"+order["user_id"]}, False)
    except JSONDecodeError:
        return util.response({"message": "Something went wrong with json in payment"}, False)
    except LWTException:
        return util.response({"message": "Something was not found"}, False)


@app.route("/payment/cancelPayment/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
# Functionality for cancelling a payment
def cancel_payment(user_id, order_id):
    try:
        # check if the payment id is valid
        payment = Payment.objects(order_id=order_id).if_exists().get().get_data()
    except DoesNotExist:
        return util.response({"message": "Payment does not exist"}, False)
    if payment["user_id"] == str(user_id):
        amount = payment["amount"]
        # and get the status code of the payment
        if Payment.objects(order_id=order_id).get().get_status()['status']:
            # if the payment has been done then rollback -> return the credits and set the payment status to false
            add_response = requests.post(
                'http://{0}/users/credit/add/{1}/{2}'.format(user_ip, payment['user_id'], amount))
            if not add_response:
                return util.response({"message": "Something went wong when adding credit to user"}, False)
            Payment.objects(order_id=order_id).update(status=False)
            return util.response(Payment.objects(order_id=order_id).get().get_data(), True)
        else:
            return util.response({"message": "The payment has already been canceled"}, False)
    else:
        return util.response({"message": "The user had never paid"}, False)


@app.route("/payment/status/<uuid:order_id>", methods=["GET"])
@json_api
# Functionality for retrieving the status of a payment
def get_status(order_id):
    payments = Payment.objects.filter(order_id=order_id)
    if len(payments.all()) != 1:
        return util.response({"message": "get status is not valid"}, False)
    else:
        return util.response(Payment.objects(order_id=order_id).if_exists().get().get_status(), True)
