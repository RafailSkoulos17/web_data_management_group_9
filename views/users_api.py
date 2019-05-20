from models.user import User
from cassandra.cqlengine.query import LWTException
from flask import Blueprint, Response, render_template, request
from cassandra.cqlengine import connection
import util
from functools import wraps
import json
import flask
import uuid
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

users_api = Blueprint("users_api", __name__)
connection.setup(['127.0.0.1'], "cqlengine")


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@users_api.route("/")
def home():
    return 'Welcome to our Web App :)'


# @api.route("/create/")
# def user_form():
#     return render_template('my_form.html')


@users_api.route("/create/", methods=["POST"])
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
        raise ValueError('User with email: %s already exists' % data["email"])
    # user = Person.create(first_name=request.form["firstname"], last_name=request.form["lastname"])


@users_api.route("/remove/<uuid:user_id>", methods=["DELETE"])
@json_api
def remove_user(user_id):
    try:
        User.objects(id=user_id).if_exists().delete()
    except LWTException as e:
        print('User not found')
        pass
    return


@users_api.route("/find/<uuid:user_id>")
@json_api
def find_user(user_id):
    try:
        user = User.objects(id=user_id).if_exists().get()
        return user.get_full_name()
    except LWTException as e:
        print('User not found')
        pass
    return


@users_api.route("/credit/<uuid:user_id>")
@json_api
def find_credit(user_id):
    try:
        user = User.objects(id=user_id).if_exists().get()
        return user.get_credit()
    except LWTException as e:
        print("User's credit not found")
        pass
    return


@users_api.route("/credit/add/<uuid:user_id>/<amount>", methods=["POST"])
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


@users_api.route("/credit/subtract/<uuid:user_id>/<amount>", methods=["POST"])
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