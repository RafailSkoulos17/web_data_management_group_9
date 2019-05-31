from sqlalchemy.orm.exc import NoResultFound

from __init__ import db, app
from flask import request, render_template, make_response
from models import user
import util
from flask import Response
from functools import wraps
import json
import flask
import logging
from util import response
import random
import uuid

db.create_all()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/user/create/", methods=["POST"])
@json_api
def create_user():
    try:
        data = json.loads(flask.request.data)
        user_1 = user.User(id=uuid.uuid4(),
                            first_name=data["first_name"],
                            last_name=data["last_name"],
                            credit=data["credit"],
                            email=data["email"])

        db.session.add(user_1)
        db.session.commit()
        logger.info('Creating user {0} {1} with id={2}'.format(user_1.first_name, user_1.last_name, user_1.id))
        return response(user_1.get_data(), True)
    except KeyError as e:
        if e.message == 'credit':
            user_1 = user.User(id=uuid.uuid4(),
                                first_name = data["first_name"],
                                last_name = data["last_name"],
                                email = data["email"])

            db.session.add(user_1)
            logger.info('Creating user {0} {1} with id={2}'.format(user_1.first_name, user_1.last_name, user_1.id))
            return response(user_1.get_data(), True)
        else:
            return response({"message": 'firstname, lastname, and email required'}, False)
    except NoResultFound:
        return response({'message': 'User with email: %s already exists' % data["email"]}, False)

@app.route("/users/remove/<uuid:user_id>", methods=["DELETE"])
@json_api
def remove_user(user_id):
    try:
        obj = user.User.query.filter_by(id=user_id).one()
        db.session.delete(obj)
        db.session.commit()
        return response({'message': 'User removed successfully'}, True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)


@app.route("/users/find/<uuid:user_id>")
@json_api
def find_user(user_id):
    try:
        user_1 = user.User.query.filter_by(id=user_id).one()
        return response(user_1.get_full_name(), True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)

@app.route("/users/credit/<uuid:user_id>")
@json_api
def find_credit(user_id):
    try:
        user_1 = user.User.query.filter_by(id=user_id).one()
        return response(user_1.get_credit(), True)
    except NoResultFound:
        return response({'message': "User's credit not found"}, False)


@app.route("/users/credit/add/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
def add_credit(user_id, amount):
    try:
        user_1 = user.User.query.filter_by(id=user_id).one()
        user_1.credit = user_1.credit + float(amount)
        db.session.commit()
        return response(user_1.get_credit(), True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)


@app.route("/users/credit/subtract/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
def subtract_credit(user_id, amount):
    try:
        user_1 = user.User.query.filter_by(id=user_id).one()
        curr_credit = user_1.credit
        if curr_credit - float(amount) < 0:
            return response({'message': 'Not enough money BITCH!!!!!'}, False)
        else:
            user_1.credit = curr_credit - float(amount)
            db.session.commit()
            return response(user_1.get_credit(), True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)
    except ValueError as v_err:
        return response({'message': v_err.message}, False)




if __name__ == '__main__':
    app.run(debug=True)


