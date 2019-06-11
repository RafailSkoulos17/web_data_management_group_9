from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from flask import Flask, jsonify
from flask import Response
import util
from functools import wraps
import json
import flask
from models.user import User
from cassandra.cqlengine.query import LWTException
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
import uuid
from util import response

# establish the Flask app
app = Flask(__name__)
app.debug = True  # for testing reasons
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')  # authorization provider
cluster = Cluster(['3.18.214.57', '3.14.6.247', '18.223.205.111'], protocol_version=2, auth_provider=auth_provider)
session = cluster.connect()  # connect to the Cassandra cluster
# session.execute("DROP KEYSPACE IF EXISTS userspace;")  # for testing reasons
# and create the keyspace if not existing
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS userspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['3.18.214.57', '3.14.6.247', '18.223.205.111'], "cqlengine", protocol_version=2, auth_provider=auth_provider)
sync_table(User)


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@app.route("/")
def home():
    return jsonify(result={"status": 200}) # 'Welcome to User API :)'


# Functionality for creating a user
@app.route("/users/create/", methods=["POST"])
@json_api
def create_user():
    try:
        data = json.loads((flask.request.data).decode('utf-8'))
        user = User.if_not_exists().create(id=uuid.uuid4(), first_name=data["first_name"], last_name=data["last_name"],
                                           credit=data["credit"], email=data["email"])
        user.save()
        return response(user.get_data(), True)
    # exception for when no credit field has been provided by the user
    except KeyError as e:
        if str(e) == "'credit'":
            user = User.create(id=uuid.uuid4(), first_name=data["first_name"], last_name=data["last_name"],
                               email=data["email"])
            user.save()
            return response(user.get_data(), True)
        else:
            return response({"message": 'firstname, lastname, and email required'}, False)
    # exception for when the user already exists
    except LWTException:
        return response({'message': 'User with email: %s already exists' % data["email"]}, False)


@app.route("/users/remove/<uuid:user_id>", methods=["DELETE"])
@json_api
# Functionality for removing a user
def remove_user(user_id):
    try:
        User.objects(id=user_id).if_exists().delete()
    # if a user did not exist
    except LWTException:
        return response({'message': 'User not found'}, False)
    return response({'message': 'User removed successfully'}, True)


@app.route("/users/find/<uuid:user_id>")
@json_api
# Functionality for finding a user
def find_user(user_id):
    try:
        user = User.objects(id=user_id).if_exists().get()
        return response(user.get_data(), True)
    # if a user did not exist
    except LWTException:
        return response({'message': 'User not found'}, False)


@app.route("/users/credit/<uuid:user_id>")
@json_api
# Functionality for finding the credits balance of a user
def find_credit(user_id):
    try:
        user = User.objects(id=user_id).if_exists().get()
        return response(user.get_credit(), True)
    # if a user did not exist
    except LWTException:
        return response({'message': "User's credit not found"}, False)


@app.route("/users/credit/add/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
# Functionality for adding credits balance to a user
def add_credit(user_id, amount):
    try:
        curr_credit = User.objects(id=user_id).if_exists().get().get_credit()['credit']
        User.objects(id=user_id).update(credit=curr_credit + float(amount))
        return response(User.objects(id=user_id).if_exists().get().get_credit(), True)
    # if a user did not exist
    except LWTException:
        return response({'message': 'User not found'}, False)


@app.route("/users/credit/subtract/<uuid:user_id>/<amount>", methods=["POST"])
@json_api
# Functionality for removing credits from a user
def subtract_credit(user_id, amount):
    try:
        curr_credit = User.objects(id=user_id).if_exists().get().get_credit()['credit']
        if curr_credit - float(amount) < 0:  # check if sufficient credits available
            return response({'message': 'Not enough money !!!!!'}, False)
        else:
            User.objects(id=user_id).update(credit=curr_credit - float(amount))
            return response(User.objects(id=user_id).if_exists().get().get_credit(), True)
    except LWTException:
        return response({'message': 'User not found'}, False)
    except ValueError as v_err:
        return response({'message': str(v_err)}, False)
