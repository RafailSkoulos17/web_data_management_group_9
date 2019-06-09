from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleas:12345678@database-1.cskyofsyxiuk.us-east-1.rds.amazonaws.com:5432/achilleasvlogiaris'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://webDataMPayment:12345678@paymentdb.cf9pwjffpznu.us-east-1.rds.amazonaws.com:5432/PaymentDB'
db = SQLAlchemy(app)

from payment import Payment
import util
from flask import Response
from functools import wraps
import json
import flask
from util import response
import uuid
import requests

user_ip = '3.91.13.122:8080'
stock_ip = '3.91.13.122:8083'
order_ip = '3.91.13.122:8081'
payment_ip = '3.91.13.122:8082'

db.create_all()

def json_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        json_result = util.to_json(result)
        return Response(response=json_result, status=200, mimetype="application/json")

    return decorated_function

@app.route("/payment/pay/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def pay(user_id, order_id):
    try:
        user_id = str(user_id)
        order_id = str(order_id)
        user = requests.get("http://{0}/users/find/".format(user_ip,user_id))
        if not user.json()['success']:
            return response({"message":"User not found"},False)
        order = requests.get("http://{0}/orders/find/".format(order_ip,order_id))
        if not order.json()['success']:
            return response({"message":"Order not found"},False)
        user = json.loads(user.text)
        order = json.loads(order.text)
        if len(user) == 0:
            return response({"message":"User not found"},False)
        elif len(order) == 0:
            return response({"message":"Order not found"},False)
        else:
            if(order["user_id"] == user["id"]):
                if(float(user["credit"]) >= float(order["amount"])):
                     subtract_response = requests.post(
                     'http://{0}/users/credit/subtract/{1}/{2}'.format(user_ip, user_id, order["amount"]))
                     sub_response = subtract_response.json()['success']
                     payment_1 = Payment(user_id = user_id,order_id = order_id, status=True,amount=order["amount"],payment_id=uuid.uuid4())
                     db.session.add(payment_1)
                     db.session.commit()
                     return response(payment_1.get_data(), True)
                else:
                     return response({"message":"Not enough credits"},False)
            else:
                return response({"message":"Wrong order"+order["user_id"]}, False)
    except NoResultFound:
        return response({"message":"the operation is not valid"}, False)

@app.route("/payment/cancelPayment/<uuid:user_id>/<uuid:order_id>", methods=["POST"])
@json_api
def cancel_payment(user_id,order_id):
    try:
        payment_1 = Payment.query.filter_by(order_id=order_id).one()
        if(str(payment_1.user_id) == str(user_id)):
            if(payment_1.status == True):
                add_response = requests.post(
                    'http://{0}/users/credit/add/{1}/{2}'.format(user_ip, user_id, int(payment_1.amount)))
                if add_response is None:
                    return response({'message':'Something went wrong with credits reimbursement'},False)
                payment_1.status = False
                db.session.add(payment_1)
                db.session.commit()
            else:
                return response({'message':'the payment has already been cancelled'},False)
    except NoResultFound:
        return response({"message":"the operation is not valid"}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)

@app.route("/payment/status/<uuid:order_id>", methods=["GET"])
@json_api
def get_status(order_id):
    try:
        payment_1 = Payment.query.filter_by(order_id=order_id).one()
        return response(payment_1.get_status(), True)
    except NoResultFound:
         return response({"message":"No order id"}, False)
    except OperationalError:
        return response({'message': 'Operational Error !!!'}, False)
