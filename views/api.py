from flask import Blueprint, Response
from cassandra.cqlengine import connection
from models.user import Person
import util
from functools import wraps
import json
import flask

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


@api.route("/create/", methods=["POST"])
@json_api
def create_user():
    data = json.loads(flask.request.data)
    user = Person.create(first_name=data["first_name"], last_name=data["last_name"])
    user.save()
    return user.get_data()


@api.route("/get-users/")
@json_api
def get_users():
    users = Person.objects().all()
    return [user.get_data() for user in users]
