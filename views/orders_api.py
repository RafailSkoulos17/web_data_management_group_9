from models.user import User
from cassandra.cqlengine.query import LWTException, DoesNotExist
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
        if "product" not in data:
            data["product"] = {}
        data["product"] = {uuid.UUID(k): v for k, v in data["product"].items()}
        order = Order.create(first_name=user["first_name"], last_name=user["last_name"], product=data["product"],
                             user_id=user["id"], order_id=order_id, payment_status=False)
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
    try:
        order = Order.objects(order_id=order_id).if_exists().get()
    except DoesNotExist:
        return {"message": "Order does not exist"}
    return order.get_data()


@order_api.route("/orders/addItem/<uuid:order_id>/<uuid:item_id>", methods=["POST"])
@json_api
def add_item(order_id, item_id):
    try:
        current_product = Order.objects(order_id=order_id).if_exists().get().get_data()["product"]
    except DoesNotExist:
        return {"message": "Order does not exist"}
    if item_id in current_product:
        current_product[item_id] += 1
    else:
        current_product[item_id] = 1
    try:
        Order.objects(order_id=order_id).if_exists().update(product=current_product)
    except DoesNotExist:
        return {"message": "Order does not exist"}
    except LWTException:
        return {"message": "Order or item not found"}
    return Order.objects(order_id=order_id).if_exists().get().get_data()


@order_api.route("/orders/removeItem/<uuid:order_id>/<uuid:item_id>", methods=["DELETE"])
@json_api
def remove_item(order_id, item_id):
    try:
        current_product = Order.objects(order_id=order_id).if_exists().get().get_data()["product"]
    except DoesNotExist:
        return {"message": "Order does not exist"}
    try:
        if item_id in current_product:
            if current_product[item_id] > 1:
                current_product[item_id] -= 1
                Order.objects(order_id=order_id).if_exists().update(product__update=current_product)
            else:
                Order.objects(order_id=order_id).if_exists().update(product__remove={item_id})
        else:
            return {"message": "The item given does not exist"}
    except DoesNotExist:
        return {"message": "Order does not exist"}
    except LWTException:
        return {"message": "Order or item not found"}
    return Order.objects(order_id=order_id).if_exists().get().get_data()
