from models.user import User
from cassandra.cqlengine.query import LWTException, DoesNotExist
from flask import Blueprint, Response
from cassandra.cqlengine import connection
from models.stocks import Stocks
import util
from functools import wraps
import json
import flask
import uuid
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stocks_api = Blueprint("stocks_api", __name__)
connection.setup(['127.0.0.1'], "cqlengine")


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


@stocks_api.route("/stock/item/create/", methods=["POST"])
@json_api
def create_product():
    try:    
        data = json.loads(flask.request.data)
        stocks = Stocks.if_not_exists().create(product_id=uuid.uuid4(), product_name=data["product_name"], stock=1,
                                           availability = 1)
        logger.info('Creating Product {0} with id={1}'.format(stocks.product_name, stocks.product_id))
        stocks.save()
        return stocks.get_data()
    except LWTException:
        ValueError:'Product already exists'


@stocks_api.route("/stock/availability/<uuid:product_id>", methods=["POST"])
@json_api
def get_product(product_id):
    try:
        return Stocks.objects(product_id=product_id).if_exists().get().get_data()
    except LWTException:
        ValueError:'Product not found'
        pass
    return

@stocks_api.route("/stock/add/<uuid:product_id>/<addition>", methods=["POST"])
@json_api
def add_product(product_id,addition):
    try:    
        curr_stock = Stocks.objects(product_id=product_id).if_exists().get().get_data()['stock']
        stocks = Stocks.objects(product_id=product_id).if_exists().update(stock = curr_stock + int(addition), availability = True)
        return Stocks.objects(product_id=product_id).if_exists().get().get_data()
    except LWTException:
        ValueError:'Product not found'
        pass
    return  

@stocks_api.route("/stock/subtract/<uuid:product_id>/<subtract>", methods=["POST"])
@json_api
def subtract_product(product_id,subtract):
    try:    
            curr_stock = Stocks.objects(product_id=product_id).if_exists().get().get_data()['stock']

            if curr_stock - int(subtract) < 0:
                ValueError:'Not enough stock'
            else:
                Stocks.objects(product_id=product_id).if_exists().update(stock = curr_stock - int(subtract))
                if curr_stock - int(subtract) == 0:
                    Stocks.objects(product_id=product_id).if_exists().update(availability = False)
            return Stocks.objects(product_id=product_id).if_exists().get().get_data() 
    except LWTException as e:
        print('Product not found')
        pass
    except ValueError as v_err:
        return {"message": v_err.message}
    return    
        
