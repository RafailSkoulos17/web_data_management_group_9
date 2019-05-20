from models.user import User
from cassandra.cqlengine.query import LWTException
from flask import Blueprint, Response
from cassandra.cqlengine import connection
from models.order import Order
import util
from functools import wraps
import json
import flask
import uuid
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

order_api = Blueprint("orders_api", __name__)
connection.setup(['127.0.0.1'], "cqlengine")


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@order_api.route("/orders/create/<uuid:user_id>", methods=["POST"])
@json_api
def create_order(user_id):
    data = json.loads(flask.request.data)
    users = User.objects.filter(id=user_id)
    if len(users.all()) != 1:
        return {"message": "User id is not valid"}
    else:
        user = users.all()[0]
        order_id = uuid.uuid4()
        order = Order.create(first_name=user["first_name"], last_name=user["last_name"], product=data["product"],
                             amount=data["amount"], user_id=user["id"], order_id=order_id)
        order.save()
        return order.get_data()


@order_api.route("/orders/remove/<uuid:order_id>", methods=["DELETE"])
@json_api
def delete_order(order_id):
    try:
        Order.objects(order_id=order_id).if_exists().delete()
    except LWTException:
        return {"message": "Order cannot be removed"}
    return {"message": "Order was removed"}


@order_api.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
def find_order(order_id):
    orders = Order.objects.filter(order_id=order_id)
    if len(orders.all()) != 1:
        return {"message": "Order id is not valid"}
    else:
        order = orders.all()[0]
    return order.get_data()
