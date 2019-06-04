from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from aws_scripts.postgres_scripts.stockapp.models.stock import Stocks
import util
from flask import Response
from functools import wraps
import json
import flask
import logging
from util import response
import uuid

app = Flask(__name__)
app.debug = True
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Boni1_21101992@localhost/postgres'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleasvlogiaris:amaji5035@5432@localhost/achilleasvlogiaris'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleas:12345678@5432@database-1.cskyofsyxiuk.us-east-1.rds.amazonaws.com/achilleasvlogiaris'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleas:12345678@database-1.cskyofsyxiuk.us-east-1.rds.amazonaws.com:5432/achilleasvlogiaris'
db = SQLAlchemy(app)

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


@app.route("/stock/item/create/", methods=["POST"])
@json_api
def create_product():
    try:
        data = json.loads(flask.request.data)
        stocks_1 = Stocks(product_id=uuid.uuid4(), product_name=data["product_name"],price=data["price"],stock=1,availability=True)
        db.session.add(stocks_1)
        db.session.commit()
        logger.info('Creating Product {0} with id={1}'.format(stocks_1.product_name, stocks_1.product_id))
        return response(stocks_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Product cannot be created'}, False)

@app.route("/stock/availability/<uuid:product_id>", methods=["GET"])
@json_api

def get_product(product_id):
    try:
        stocks_1 = Stocks.query.filter_by(product_id=product_id).one()
        return response(stocks_1.get_data(),True)
    except NoResultFound:
        return response({'message': 'Product cannot be found'}, False)

@app.route("/stock/add/<uuid:product_id>/<addition>", methods=["POST"])
@json_api
def add_product(product_id, addition):
    try:
        stocks_1 = Stocks.query.filter_by(product_id=product_id).one()
        stocks_1.stock = stocks_1.stock + int(addition)
        db.session.commit()
        return response(stocks_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)

@app.route("/stock/subtract/<uuid:product_id>/<subtraction>", methods=["POST"])
@json_api
def subtract_product(product_id, subtraction):
    try:
        stocks_1 = Stocks.query.filter_by(product_id=product_id).one()
        if(stocks_1.stock >= int(subtraction)):
            stocks_1.stock = stocks_1.stock - int(subtraction)
            db.session.commit()
            return response(stocks_1.get_data(), True)
        else:
            return response({'message': 'Not enough stocks'}, False)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)
