from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import CompileError,DataError

#Connect to the AWS RDS postgres instance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://User_database:12345678@userinstance.cacpqjasklix.us-east-1.rds.amazonaws.com:5432/User_database'
db = SQLAlchemy(app)

from user import User
import util
from flask import Response
from functools import wraps
import json
import flask
from util import response
import uuid

#Create or update tables in the database
db.create_all()

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


#Create a new user with unique email id
@app.route("/users/create/", methods=["POST"])
@json_api
def create_user():
    try:
        data = json.loads((flask.request.data).decode('utf-8'))
        user_1 = User(id=uuid.uuid4(),
                            first_name=data["first_name"],
                            last_name=data["last_name"],
                            credit=data["credit"],
                            email=data["email"])

        db.session.add(user_1)
        db.session.commit()
        return response(user_1.get_data(), True)
    except KeyError as e:
        if e.message == 'credit':
            user_1 = User(id=uuid.uuid4(),
                                first_name = data["first_name"],
                                last_name = data["last_name"],
                                email = data["email"])

            db.session.add(user_1)
            return response(user_1.get_data(), True)
        else:
            return response({"message": 'firstname, lastname, and email required'}, False)
    except DataError:
        return response({'message': 'User with email: %s already exists' % data["email"]}, False)


#Delete a user from the user table
@app.route("/users/remove/<uuid:user_id>", methods=["DELETE"])
@json_api
def remove_user(user_id):
    try:
        obj = User.query.filter_by(id=user_id).one()
        db.session.delete(obj)
        db.session.commit()
        return response({'message': 'User removed successfully'}, True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Find user from the user table
@app.route("/users/find/<uuid:user_id>")
@json_api
def find_user(user_id):
    try:
        user_1 = User.query.filter_by(id=user_id).one()
        return response(user_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)
    except OperationalError as e:
        return response({'message': e}, False)


#Find user credits
@app.route("/users/credit/<uuid:user_id>")
@json_api
def find_credit(user_id):
    try:
        user_1 = User.query.filter_by(id=user_id).one()
        return response(user_1.get_credit(), True)
    except NoResultFound:
        return response({'message': "User's credit not found"}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Add money to user credits
@app.route("/users/credit/add/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
def add_credit(user_id, amount):
    try:
        user_1 = User.query.filter_by(id=user_id).one()
        user_1.credit = user_1.credit + float(amount)
        db.session.commit()
        return response(user_1.get_credit(), True)
    except NoResultFound:
        return response({'message': 'User not found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Subtract money from user credits
@app.route("/users/credit/subtract/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
def subtract_credit(user_id, amount):
    try:
        user_1 = User.query.filter_by(id=user_id).one()
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
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)
