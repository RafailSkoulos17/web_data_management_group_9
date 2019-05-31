from models.user import User
from flask import Blueprint, Response
from models.stocks import Stocks
import util
from functools import wraps
import json
import flask
import uuid
import logging
from util import response

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stocks_api = Blueprint("stocks_api", __name__)


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
                                               availability=1)
        logger.info('Creating Product {0} with id={1}'.format(stocks.product_name, stocks.product_id))
        stocks.save()
        return response(stocks.get_data(), True)
    except LWTException:
        return response({'message': 'Product already exists'}, False)


@stocks_api.route("/stock/availability/<uuid:product_id>", methods=["POST"])
@json_api
def get_product(product_id):
    try:
        return response(Stocks.objects(product_id=product_id).if_exists().get().get_data(), True)
    except LWTException:
        return response({'message': 'Product not found'}, False)


@stocks_api.route("/stock/add/<uuid:product_id>/<addition>", methods=["POST"])
@json_api
def add_product(product_id, addition):
    try:
        curr_stock = Stocks.objects(product_id=product_id).if_exists().get().get_data()['stock']
        stocks = Stocks.objects(product_id=product_id).if_exists().update(stock=curr_stock + int(addition),
                                                                          availability=True)
        return response(Stocks.objects(product_id=product_id).if_exists().get().get_data(), True)
    except LWTException:
        return response({'message': 'Product not found'}, False)


@stocks_api.route("/stock/subtract/<uuid:product_id>/<subtract>", methods=["POST"])
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
    except LWTException as e:
        return response({'message': 'Product not found'}, False)
    except ValueError as v_err:
        return response({"message": v_err.message}, False)
