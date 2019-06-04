    
from sqlalchemy.orm.exc import NoResultFound
import models.users as users
import models.stocks as stocks
import models.orders as order
import models.payment as payment
from __init__ import db, app
from flask import request, render_template, make_response
from models import users
import util
from flask import Response
from functools import wraps
import json
import flask
import logging
from util import response
import random
import uuid
import requests
import yaml

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
        user_1 = users.User(id=uuid.uuid4(),
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
        user_1 = users.User.query.filter_by(id=user_id).one()
        return response(user_1.get_data(), True)
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
        user_1 = users.User.query.filter_by(id=user_id).one()
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

#-----------------------------------------------------------------------------------
#Stocks module
@app.route("/stock/item/create/", methods=["POST"])
@json_api
def create_product():
    try:
        data = json.loads(flask.request.data)
        stocks_1 = stocks.Stocks(product_id=uuid.uuid4(), product_name=data["product_name"],price=data["price"],stock=1,availability=True)
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
        stocks_1 = stocks.Stocks.query.filter_by(product_id=product_id).one()
        return response(stocks_1.get_data(),True)
    except NoResultFound:
        return response({'message': 'Product cannot be found'}, False)

@app.route("/stock/add/<uuid:product_id>/<addition>", methods=["POST"])
@json_api
def add_product(product_id, addition):
    try:
        stocks_1 =  stocks.Stocks.query.filter_by(product_id=product_id).one()
        stocks_1.stock = stocks_1.stock + int(addition)
        db.session.commit()
        return response(stocks_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)

@app.route("/stock/subtract/<uuid:product_id>/<subtraction>", methods=["POST"])
@json_api
def subtract_product(product_id, subtraction):
    try:
        stocks_1 =  stocks.Stocks.query.filter_by(product_id=product_id).one()
        if(stocks_1.stock >= int(subtraction)):
            stocks_1.stock = stocks_1.stock - int(subtraction)
            db.session.commit()
            return response(stocks_1.get_data(), True)
        else:
            return response({'message': 'Not enough stocks'}, False)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)

#------------------------------------------------------------------------------------
#Order Module

@app.route("/orders/create/<uuid:user_id>", methods=["POST"])
@json_api
def create_order(user_id):
    try:
        data = json.loads(flask.request.data)
        user_id = str(user_id)
        users = requests.get("http://127.0.0.1:5000/users/find/"+user_id)
        users = json.loads(users.text)
        if len(users) == 0:
            return response({"message":"User not found"})

        else:
            if "items" not in data:
                return response({"message":"Items not specified"},False)
            Amount = 0.0
            new_items = yaml.load(data["items"])
            for keys,values in new_items.items():
                product = requests.get("http://127.0.0.1:5000/stock/availability/"+str(keys))
                product = json.loads(product.text)
                Amount += product["price"]*values
            order_1 = order.Order(items=data["items"],user_id=user_id, order_id=uuid.uuid4(),amount = Amount,payment_status=False) 
            db.session.add(order_1)
            db.session.commit()
            return response(order_1.get_data(),True)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)

@app.route("/orders/remove/<uuid:order_id>", methods=["DELETE"])
@json_api
def delete_order(order_id):
    try:
        obj = order.Order.query.filter_by(order_id=order_id).one()
        db.session.delete(obj)
        db.session.commit()
        return response({'message': 'Order deleted successfully'}, True)
    except NoResultFound:
        return response({'message': 'Order not found'}, False)

@app.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
def find_order(order_id):
    try:
        order_id = str(order_id)
        order_1 = order.Order.query.filter_by(order_id=order_id).one()
        return response(order_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Order not found'}, False)

@app.route("/orders/addItem/<uuid:order_id>/<uuid:item_id>/<quantity>", methods=["POST"])
@json_api
def add_item(order_id,item_id,quantity):
    try:
        order_id = str(order_id)
        order_1 = order.Order.query.filter_by(order_id=order_id).one()
        product = requests.get("http://127.0.0.1:5000/stock/availability/"+str(item_id))
        product = json.loads(product.text)  
        new_items = dict(order_1.items)
        if(str(item_id) not in new_items.keys()):
            new_items[str(item_id)] = int(quantity)
            order_1.items = new_items
            order_1.amount = product["price"]*int(quantity)
            db.session.commit()
            return response(order_1.get_data(), True)
        else:
            return response({'message':'item already present in order'},False)
    except NoResultFound:
        return response({'message':'order not found'}, False)

@app.route("/orders/removeItem/<uuid:order_id>/<uuid:item_id>", methods=["DELETE"])
@json_api
def remove_item(order_id, item_id):
    try:

        order_id = str(order_id)
        order_1 = order.Order.query.filter_by(order_id=order_id).one()
        product = requests.get("http://127.0.0.1:5000/stock/availability/"+str(item_id))
        product = json.loads(product.text)
        new_items = dict(order_1.items)
        if(str(item_id) in new_items.keys()):
            order_1.amount -= product["price"]*new_items[str(item_id)]
            new_items.pop(str(item_id))
            order_1.items = new_items
            return str(order_1.items)
            db.session.commit()
            return response(order_1.get_data(), True)
        else:
            return response({'message':'item is not present in order'}, False)
    except NoResultFound:
        return response({'message':'order not found'}, False)


@app.route("/orders/checkout/<uuid:order_id>", methods=["POST"])
@json_api
def checkout(order_id):
    order_id = str(order_id)
    current_order = requests.get("http://127.0.0.1:5000/orders/find/"+order_id)
    current_order = current_order.json()
    # return str(current_order['user_id'])
    # current_order = json.loads(current_order.text)
    pay_response = requests.post(
        'http://127.0.0.1:5000/payment/pay/{0}/{1}'.format(current_order['user_id'], current_order['order_id']))
    if not pay_response.json()['success']:
        return response({"message": "Something went wrong with the payment"}, False)
    
    prods_subtracted = {}
    products = yaml.load(current_order["items"])
    # return type(products)
    for prod, num in products.items():
        sub_response = requests.post(
            'http://127.0.0.1:5000/stock/subtract/{0}/{1}'.format(prod, num))
        if not sub_response.json()['success']:
        # if not json.loads(sub_response.content)['success']:
            pay_response = requests.post(
                'http://127.0.0.1:5000/payment/cancelPayment/{0}/{1}'.format(current_order['user_id'], current_order['order_id']))

            for sub_prod, sub_num in prods_subtracted.items():
                sub_response = requests.post(
                    'http://127.0.0.1:5000/stock/add/{0}/{1}'.format(sub_prod, sub_num))

            return response({'message': 'Stock {1} with quantity {0} is not available'.format(num, prod)}, False)
        else:
            prods_subtracted[prod] = num
        order_1 = order.Order.query.filter_by(order_id=order_id).one()
        order_1.payment_status = True
        db.session.commit()
        return response({'message': 'Checkout was completed successfully'}, True)

#-------------------------------------------------------------------------------------
#Payment
@app.route("/payment/pay/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def pay(user_id, order_id):
    user_id = str(user_id)
    order_id = str(order_id)
    user = requests.get("http://127.0.0.1:5000/users/find/"+user_id)
    order = requests.get("http://127.0.0.1:5000/orders/find/"+order_id)
    user = json.loads(user.text)
    order = json.loads(order.text)
    if len(user) == 0:
        return response({"message":"User not found"})
    elif len(order) == 0:
        return response({"message":"Order not found"})
    else:
        if(order["user_id"] == user["id"]):
            if(user["credit"] >= order["amount"]):
                subtract_response = requests.post(
                'http://127.0.0.1:5000/users/credit/subtract/{0}/{1}'.format(user_id, order["amount"]))
                sub_response = subtract_response.json()['success']
                payment_1 = payment.Payment(user_id = user_id,order_id = order_id, status=True,amount=order["amount"],payment_id=uuid.uuid4())
                db.session.add(payment_1)
                db.session.commit()
                return response(payment_1.get_data(), True)
            else:
                return response({"message":"Not enough credits"},False)
        else:
            return response({"message":"Wrong order"+order["user_id"]}, False)

@app.route("/payment/cancelPayment/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def cancel_payment(user_id,order_id):
    try:
        payment_1 = payment.Payment.query.filter_by(order_id=order_id).one()
        if(str(payment_1.user_id) == str(user_id)):
            add_response = requests.post(
                'http://127.0.0.1:5000/users/credit/add/{0}/{1}'.format(user_id, int(payment_1.amount)))
            payment_1.status = False
            db.session.add(payment_1)
            db.session.commit()
    except NoResultFound:
        return response({"message":"the operation is not valid"}, False)

@app.route("/payment/status/<uuid:order_id>", methods=["GET"])
@json_api
def get_status(order_id):
    payment_1 = payment.Payment.query.filter_by(order_id=order_id).one()
    return response(payment_1.get_status(), True)

if __name__ == '__main__':
    app.run(debug=True)
