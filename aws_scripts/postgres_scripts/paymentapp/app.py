from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from aws_scripts.postgres_scripts.paymentapp.models.payment import Payment
import util
from flask import Response
from functools import wraps
import json
import logging
from util import response
import uuid
import requests

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
                payment_1 = Payment(user_id = user_id,order_id = order_id, status=True,amount=order["amount"],payment_id=uuid.uuid4())
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
        payment_1 = Payment.query.filter_by(order_id=order_id).one()
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
    payment_1 = Payment.query.filter_by(order_id=order_id).one()
    return response(payment_1.get_status(), True)

if __name__ == '__main__':
    app.run(debug=True)
