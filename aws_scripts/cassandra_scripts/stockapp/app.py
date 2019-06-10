from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from flask import Flask, Response
import util
from functools import wraps
import json
import flask
from models.stocks import Stocks
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import LWTException, DoesNotExist
import uuid
from util import response

app = Flask(__name__)
app.debug = True
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cluster = Cluster(['3.14.247.82', '18.188.104.49', '3.19.26.234'],protocol_version=2, auth_provider=auth_provider)
session = cluster.connect()
#session.execute("DROP KEYSPACE IF EXISTS stockspace;")
session.execute(
        "CREATE KEYSPACE IF NOT EXISTS stockspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':2};")
connection.setup(['3.14.247.82', '18.188.104.49', '3.19.26.234'], "cqlengine", protocol_version=2,auth_provider=auth_provider)
sync_table(Stocks)


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@app.route("/")
def home():
    return 'Welcome to Stock API :)'


@app.route("/stock/item/create/", methods=["POST"])
@json_api
def create_product():
    try:
        data = json.loads((flask.request.data).decode('utf-8'))
        stocks = Stocks.if_not_exists().create(product_id=uuid.uuid4(), product_name=data["product_name"], stock=1,
                                               availability=1, price=data["price"])
        stocks.save()
        return response(stocks.get_data(), True)
    except LWTException:
        return response({'message': 'Product already exists'}, False)


@app.route("/stock/availability/<uuid:product_id>")
@json_api
def get_product(product_id):
    try:
        return response(Stocks.objects(product_id=product_id).if_exists().get().get_data(), True)
    except LWTException:
        return response({'message': 'Product not found'}, False)


@app.route("/stock/add/<uuid:product_id>/<addition>", methods=["POST"])
@json_api
def add_product(product_id, addition):
    try:
        curr_stock = Stocks.objects(product_id=product_id).if_exists().get().get_data()['stock']
        stocks = Stocks.objects(product_id=product_id).if_exists().update(stock=curr_stock + int(addition),
                                                                          availability=True)
        return response(Stocks.objects(product_id=product_id).if_exists().get().get_data(), True)
    except LWTException:
        return response({'message': 'Product not found'}, False)


@app.route("/stock/subtract/<uuid:product_id>/<subtract>", methods=["POST"])
@json_api
def subtract_product(product_id, subtract):
    try:
        curr_stock = Stocks.objects(product_id=product_id).if_exists().get().get_data()['stock']

        if curr_stock - int(subtract) < 0:
            return response({'message': 'Not enough stock'}, False)
        else:
            Stocks.objects(product_id=product_id).if_exists().update(stock=curr_stock - int(subtract))
            if curr_stock - int(subtract) == 0:
                Stocks.objects(product_id=product_id).if_exists().update(availability=False)
        return response(Stocks.objects(product_id=product_id).if_exists().get().get_data(), True)
    except LWTException:
        return response({'message': 'Product not found'}, False)
    except DoesNotExist:
        return response({'message': 'Product not found'}, False)
    except ValueError as v_err:
        return response({"message": str(v_err)}, False)
