from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

#Connect to the AWS RDS postgres instance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://stock_database:12345678@stockinstance.cacpqjasklix.us-east-1.rds.amazonaws.com:5432/stock_database'
db = SQLAlchemy(app)

from stock import Stocks
import util
from flask import Response
from functools import wraps
import json
import flask
from util import response
import uuid
import requests

#Create or update tables in the database
db.create_all()


def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function


#Create a new stock
@app.route("/stock/item/create/", methods=["POST"])
@json_api
def create_product():
    try:
        data = json.loads(flask.request.data)
        stocks_1 = Stocks(product_id=uuid.uuid4(), product_name=data["product_name"],stock=1,availability=True,price=data["price"])
        db.session.add(stocks_1)
        db.session.commit()
        return response(stocks_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Product cannot be created'}, False)


#Check availability of a stock
@app.route("/stock/availability/<uuid:product_id>", methods=["GET"])
@json_api

def get_product(product_id):
    try:
        stocks_1 = Stocks.query.filter_by(product_id=product_id).one()
        return response(stocks_1.get_data(),True)
    except NoResultFound:
        return response({'message': 'Product cannot be found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Increase quantity of a stock
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
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Decrease quantity of a stock
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
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)    
