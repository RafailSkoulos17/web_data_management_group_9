from models.user import User
from cassandra.cqlengine.query import LWTException, DoesNotExist
from flask import Blueprint, Response
from cassandra.cqlengine import connection
from models.order import Order
from models.payment import Payment
from models.user import User
from views.users_api import subtract_credit, add_credit
import util
from functools import wraps
import json
import flask
import uuid
import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

payment_api = Blueprint("payments_api", __name__)
connection.setup(['127.0.0.1'], "cqlengine")


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function

@payment_api.route("/payment/pay/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def pay(user_id, order_id):
    users = User.objects.filter(id=user_id)
    orders = Order.objects.filter(order_id=order_id)
    if len(users.all()) != 1 or len(orders.all()) != 1:
        return util.response({"message": "User id or Order id is not valid"}, False)
    else:
        user = users.all()[0]
        order = orders.all()[0]
        if order["user_id"] == user["id"]:
            test = order["product"].items()
            amount = ([x[1] for x in test][0])
            product_id = ([x[0] for x in test][0])
            subtract_response = requests.post(
                'http://127.0.0.1:5000/users/credit/subtract/{0}/{1}'.format(user['id'], amount))
            sub_response = json.loads(subtract_response.content)['success']
            if not sub_response:
                return util.response({"message": "Not enough credits for the payment"}, False)
            else:
                test2 = True
                payment = Payment.create(first_name=user["first_name"], last_name=user["last_name"], email=user["email"],
                                         product=str(product_id), amount=amount, user_id=user["id"],
                                         order_id=order["order_id"], payment_id=uuid.uuid4(), status=test2)
                payment.save()
                return util.response({}, Payment.objects(order_id=order_id).if_exists().get().get_status())
        else:
            return util.response({"message": "Wrong order"}, False)




@payment_api.route("/payment/cancelPayment/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def cancel_payment(user_id, order_id):
    payments = Payment.objects.filter(order_id=order_id)
    if (len(payments.all())) != 1:
        return util.response({"message": "Cancellation is not valid"}, False)
    else:
        payment = payments.all()[0]
        if payment["user_id"] == user_id:
            print("found")
            amount = payment["amount"]
            if Payment.objects(order_id=order_id).get().get_status()['status']:
                add_response = requests.post(
                    'http://127.0.0.1:5000/users/credit/add/{0}/{1}'.format(payment['user_id'], amount))
                Payment.objects(order_id=order_id).update(status=False)
                return util.response(Payment.objects(order_id=order_id).get().get_data(), True)
            else:
                return util.response({"message": "The payment has already been canceled"}, False)
        else:
            return util.response({"message": "The user had never paid"}, False)



@payment_api.route("/payment/status/<uuid:order_id>", methods=["GET"])
@json_api
def get_status(order_id):
    payments = Payment.objects.filter(order_id=order_id)
    if len(payments.all()) != 1:
        return util.response({"message": "get status is not valid"}, False)
    else:
        return util.response(Payment.objects(order_id=order_id).if_exists().get().get_status(), True)

