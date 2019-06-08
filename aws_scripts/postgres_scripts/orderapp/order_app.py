from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleas:12345678@database-1.cskyofsyxiuk.us-east-1.rds.amazonaws.com:5432/achilleasvlogiaris'
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


@app.route("/orders/create/<uuid:user_id>", methods=["POST"])
@json_api
def create_order(user_id):
    try:
        data = json.loads(flask.request.data)
        user_id = str(user_id)
        users = requests.get("http://3.91.13.122:8080/users/find/" + user_id)
        users = json.loads(users.text)
        if len(users) == 0:
            return response({"message": "User not found"})

        else:
            if "items" not in data:
                return response({"message": "Items not specified"}, False)
            Amount = 0.0
            items_1 = data["items"]
            new_items = dict(data["items"])
            for keys, values in new_items.items():
                product = requests.get("http://3.91.13.122:8083/stock/availability/" + str(keys))
                product = json.loads(product.text)
                Amount += product["price"] * values
            order_1 = Order(items=items_1, user_id=uuid.UUID(user_id), order_id=uuid.uuid4(), amount=Amount,
                                  payment_status=False)
            db.session.add(order_1)
            db.session.commit()
            return response(order_1.get_data(), True)
    except NoResultFound:
        return response({'message': 'Stock cannot be found'}, False)


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


@app.route("/orders/find/<uuid:order_id>", methods=["GET"])
@json_api
def find_order(order_id):
    try:
        order_id = str(order_id)
        order_1 = Order.query.filter_by(order_id=order_id).one()
        return response(order_1.get_data(), True)
    except NoResultFound:
        order_1 = Order.query.filter_by(id=order_id).one()
        return response(order_1.get_full_name(), True)


@app.route("/orders/addItem/<uuid:order_id>/<uuid:item_id>/<quantity>", methods=["POST"])
@json_api
def add_item(order_id, item_id, quantity):
    try:
        order_id = str(order_id)
        order_1 = Order.query.filter_by(order_id=order_id).one()
        product = requests.get("http://3.91.13.122:8083/stock/availability/" + str(item_id))
        product = json.loads(product.text)
        new_items = dict(order_1.items)
        if (str(item_id) not in new_items.keys()):
            new_items[str(item_id)] = int(quantity)
            order_1.items = new_items
            order_1.amount  += product["price"] * int(quantity)
            db.session.commit()
            return response(order_1.get_data(), True)
        else:
            return response({'message': 'item already present in order'}, False)
    except NoResultFound:
        return response({'message': 'order not found'}, False)


@app.route("/orders/removeItem/<uuid:order_id>/<uuid:item_id>", methods=["DELETE"])
@json_api
def remove_item(order_id, item_id):
    try:

        order_id = str(order_id)
        order_1 = Order.query.filter_by(order_id=order_id).one()
        product = requests.get("http://3.91.13.122:8083/stock/availability/" + str(item_id))
        product = json.loads(product.text)
        new_items = dict(order_1.items)
        if (str(item_id) in new_items.keys()):
            order_1.amount -= product["price"] * new_items[str(item_id)]
            new_items.pop(str(item_id))
            order_1.items = new_items
            db.session.commit()
            return response(order_1.get_data(), True)
        else:
            return response({'message': 'item is not present in order'}, False)
    except NoResultFound:
        return response({'message': 'order not found'}, False)


@app.route("/orders/checkout/<uuid:order_id>", methods=["POST"])
@json_api
def checkout(order_id):
    try:
        order_id = str(order_id)
        current_order = requests.get("http://3.91.13.122:8081/orders/find/" + order_id)
    
        current_order = current_order.json()
        #return response({"status":current_order["payment_status"]},False)
        if(str(current_order["payment_status"])=="True"):
            return response({"message":"Payment has been done already"},False)
        pay_response = requests.post(
            'http://3.91.13.122:8082/payment/pay/{0}/{1}'.format(current_order['user_id'],current_order['order_id']))
        if not pay_response.json()['success']:
                return response({"message": "Something went wrong with the payment"}, False)

        prods_subtracted = {}
        products = yaml.load(current_order["items"])
        # return type(products)
        for prod, num in products.items():
            sub_response = requests.post(
                'http://3.91.13.122:8083/stock/subtract/{0}/{1}'.format(prod, num))
            if not sub_response.json()['success']:
                # if not json.loads(sub_response.content)['success']:
                pay_response = requests.post(
                    'http://3.91.13.122:8082/payment/cancelPayment/{0}/{1}'.format(current_order['user_id'],
                                                                                     current_order['order_id']))

                for sub_prod, sub_num in prods_subtracted.items():
                    sub_response = requests.post(
                        'http://3.91.13.122:8083/stock/add/{0}/{1}'.format(sub_prod, sub_num))

                return response({'message': 'Stock {1} with quantity {0} is not available'.format(num, prod)}, False)
            else:
                prods_subtracted[prod] = num
            order_1 = Order.query.filter_by(order_id=order_id).one()
            order_1.payment_status = True
            db.session.commit()
            return response({'message': 'Checkout was completed successfully'}, True)
    except NoResultFound:
        return response({'message': 'order not found'}, False)
