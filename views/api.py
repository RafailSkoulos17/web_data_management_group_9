from models.user import User
from cassandra.cqlengine.query import LWTException
from flask import Blueprint, Response, render_template, request
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

api = Blueprint("api", __name__)
connection.setup(['127.0.0.1'], "cqlengine")


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@api.route("/")
def home():
    return 'Welcome to our Web App :)'


# @api.route("/create/")
# def user_form():
#     return render_template('my_form.html')


@api.route("/create/", methods=["POST"])
@json_api
def create_user():
    try:
        data = json.loads(flask.request.data)
        user = User.if_not_exists().create(id=uuid.uuid4(), first_name=data["first_name"], last_name=data["last_name"],
                                           credit=data["credit"], email=data["email"])
        logger.info('Creating user {0} {1} with id={2}'.format(user.first_name, user.last_name, user.id))
        user.save()
        return user.get_data()
    except KeyError as e:
        if e.message == 'credit':
            user = User.create(id=uuid.uuid4(), first_name=data["first_name"], last_name=data["last_name"],
                               email=data["email"])
            user.save()
            logger.info('Creating user {0} {1} with id={2}'.format(user.first_name, user.last_name, user.id))
            return user.get_data()
        else:
            return {"message": 'firstname, lastname, and email required'}
    except LWTException:
        # Exact string in this message is expected by integration test
        raise ValueError('Exception creating user because it already exists for ' + data["email"])
    # user = Person.create(first_name=request.form["firstname"], last_name=request.form["lastname"])


@api.route("/remove/<uuid:user_id>", methods=["DELETE"])
@json_api
def remove_user(user_id):
    try:
        User.objects(id=user_id).if_exists().delete()
    except LWTException as e:
        print('User not found')
        pass
    return


@api.route("/find/<uuid:user_id>")
@json_api
def find_user(user_id):
    try:
        user = User.objects(id=user_id).if_exists().get()
        return user.get_full_name()
    except LWTException as e:
        print('User not found')
        pass
    return


@api.route("/credit/<uuid:user_id>")
@json_api
def find_credit(user_id):
    try:
        user = User.objects(id=user_id).if_exists().get()
        return user.get_credit()
    except LWTException as e:
        print("User's credit not found")
        pass
    return


@api.route("/credit/add/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
def add_credit(user_id, amount):
    try:
        curr_credit = User.objects(id=user_id).if_exists().get().get_credit()['credit']
        User.objects(id=user_id).update(credit=curr_credit+float(amount))
        return User.objects(id=user_id).if_exists().get().get_credit()
    except LWTException as e:
        print('User not found')
        pass
    return


@api.route("/credit/subtract/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
def subtract_credit(user_id, amount):
    try:
        curr_credit = User.objects(id=user_id).if_exists().get().get_credit()['credit']
        if curr_credit-float(amount) < 0:
            raise ValueError('Not enough money BITCH!!!!!')
        else:
            User.objects(id=user_id).update(credit=curr_credit - float(amount))
            return User.objects(id=user_id).if_exists().get().get_credit()
    except LWTException as e:
        print('User not found')
        pass
    except ValueError as v_err:
        return {"message": v_err.message}
    return


@api.route("/orders/create/<uuid:user_id>", methods=["POST"])
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


@api.route("/orders/remove/<uuid:order_id>", methods=["DELETE"])
@json_api
def delete_order(order_id):
    try:
        Order.objects(order_id=order_id).if_exists().delete()
    except LWTException:
        return {"message": "Order cannot be removed"}
    return {"message": "Order was removed"}


@api.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
def find_order(order_id):
    orders = Order.objects.filter(order_id=order_id)
    if len(orders.all()) != 1:
        return {"message": "Order id is not valid"}
    else:
        order = orders.all()[0]
    return order.get_data()
