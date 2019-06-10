from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import CompileError, OperationalError
#Connect to the AWS RDS postgres instance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://order_database:12345678@orderinstance.cacpqjasklix.us-east-1.rds.amazonaws.com:5432/order_database'
db = SQLAlchemy(app)

from order import Order
import util
from flask import Response
from functools import wraps
import json
import flask
from util import response
import uuid
import requests
import yaml

#Create or update tables
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

#Ips for all the services
user_ip = '3.93.185.70:8080'
stock_ip = '3.93.185.70:8083'
order_ip = '3.93.185.70:8081'
payment_ip = '3.93.185.70:8082'

#Create a new order
@app.route("/orders/create/<uuid:user_id>", methods=["POST"])
@json_api
def create_order(user_id):
    try:
        data = json.loads(flask.request.data)
        user_id = str(user_id)
        users = requests.get("http://{0}/users/find/{1}".format(user_ip,user_id))
        if not users.json()['success']:
            return response({'message':'User not found'},False)
        users = json.loads(users.text)
        if len(users) == 0:
            return response({"message": "User not found"},False)

        else:
            if "product" not in data:
                return response({"message": "Items not specified"}, False)
            Amount = 0.0
            items_1 = data["product"]
            new_items = dict(data["product"])
            for keys, values in new_items.items():
                product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(keys)))
                if not product.json()['success']:
                    return response({'message':'Product not found'},False)
                product = json.loads(product.text)
                Amount += product["price"] * values
            order_1 = Order(product=items_1, user_id=uuid.UUID(user_id), order_id=uuid.uuid4(), amount=Amount,
                                  payment_status=False)
            db.session.add(order_1)
            db.session.commit()
            return response(order_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Remove an order from the order table
@app.route("/orders/remove/<uuid:order_id>", methods=["DELETE"])
@json_api
def delete_order(order_id):
    try:
        obj = Order.query.filter_by(order_id=order_id).one()
        db.session.delete(obj)
        db.session.commit()
        return response({'message': 'Order deleted successfully'}, True)
    except NoResultFound:
        return response({'message': 'Order not found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Find an order in the order table
@app.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
def find_order(order_id):
    try:
        order_id = str(order_id)
        order_1 = Order.query.filter_by(order_id=order_id).one()
        return response(order_1.get_data(), True)
    except NoResultFound:
        return response({"message":"Order not found"}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


#Increase the quantity of an item by 1 in an order
@app.route("/orders/addItem/<uuid:order_id>/<uuid:item_id>", methods=["POST"])
@json_api
def add_item(order_id, item_id):
    try:
        order_id = str(order_id)
        order_1 = Order.query.filter_by(order_id=order_id).one()
        product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(item_id)))
        if not product.json()['success']:
            return response({'message':'product not found'},False)
        product = json.loads(product.text)
        new_items = dict(order_1.product)
        if (str(item_id) not in new_items.keys()):
            new_items[str(item_id)] = 1
        else:
            new_items[str(item_id)] += 1
        order_1.product = new_items
        order_1.amount  += product["price"]
        db.session.commit()
        return response(order_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'order not found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)

#Decrease the quantity of an item by 1 in an order
@app.route("/orders/removeItem/<uuid:order_id>/<uuid:item_id>", methods=["DELETE"])
@json_api
def remove_item(order_id, item_id):
    try:

        order_id = str(order_id)
        order_1 = Order.query.filter_by(order_id=order_id).one()
        product = requests.get("http://{0}/stock/availability/{1}".format(stock_ip,str(item_id)))
        if not product.json()['success']:
            return response({'message':'product not found'},False)
        product = json.loads(product.text)
        new_items = dict(order_1.product)
        if (str(item_id) not in new_items.keys()):
            return response({'message':'product not present in the order'},False)
        if(new_items[str(item_id)] <= 0):
            return response({"message":"Item quantity is already zero"},False)
        new_items[str(item_id)] -= 1
        order_1.product = new_items
        order_1.amount  -= product["price"]
        db.session.commit()
        return response(order_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'order not found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)


# Perform order checkout
@app.route("/orders/checkout/<uuid:order_id>", methods=["POST"])
@json_api
def checkout(order_id):
    try:
        order_id = str(order_id)
        current_order = requests.get("http://{0}/orders/find/{1}".format(order_ip,order_id))
        if not current_order.json()['success']:
            return response({"message":"Order not found"},False)
        current_order = current_order.json()
        #return response({"status":current_order["payment_status"]},False)
        if(str(current_order["payment_status"])=="True"):
            return response({"message":"Payment has been done already"},False)
        pay_response = requests.post( 'http://{0}/payment/pay/{1}/{2}'.format(payment_ip, current_order['user_id'],current_order['order_id']))
        if not pay_response.json()['success']:
            return response({'message':'Payment failed'},False)
        prods_subtracted = {}
        products = yaml.load(current_order["product"])
        # return type(products)
        for prod, num in products.items():
            sub_response = requests.post(
                'http://{0}/stock/subtract/{1}/{2}'.format(stock_ip, prod, num))
            if not sub_response.json()['success']:
                pay_response = requests.post(
                    'http://{0}/payment/cancelPayment/{1}/{2}'.format(payment_ip,current_order['user_id'],
                                                                                    current_order['order_id']))

                for sub_prod, sub_num in prods_subtracted.items():
                    sub_response = requests.post(
                        'http://{0}/stock/add/{1}/{2}'.format(stock_ip, sub_prod, sub_num))

                return response({'message': 'Stock {1} with quantity {0} is not available'.format(num, prod)}, False)
            else:
                prods_subtracted[prod] = num
            try:    
                order_1 = Order.query.filter_by(order_id=order_id).one()
                order_1.payment_status = True
                db.session.commit()
                return response({'message': 'Checkout was completed successfully'}, True)
            except OperationalError:
                return response({'message': 'Operational Error !!!'}, False)
    except NoResultFound:
        return response({'message': 'order not found'}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)
