from cassandra.cluster import Cluster
from flask import Flask

from models.order import Order
from models.stocks import Stocks
from views.users_api import users_api
from views.orders_api import order_api
from views.stocks_api import stocks_api
from views.payments_api import payment_api
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from models.user import User
from models.payment import Payment
import logging

logging.basicConfig(filename='logger.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


def create_app():
    app = Flask(__name__)
    app.debug = True

    # Register your api blueprint here
    app.register_blueprint(users_api)
    app.register_blueprint(order_api)
    app.register_blueprint(stocks_api)
    app.register_blueprint(payment_api)
    cluster = Cluster()
    session = cluster.connect()
    session.execute("DROP KEYSPACE IF EXISTS orderspace;")

    # just a main keyspace for future use
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS webdata19 WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};")

    # Example keyspaces for each service -- Don't forget to set the keyspaces in the models
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS userspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};")
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS orderspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};")
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS stockspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};")
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS paymentspace WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};")
    # cluster.connect(keyspace='webdata19')
    return app


app = create_app()

if __name__ == '__main__':
    connection.setup(['127.0.0.1'], "cqlengine", protocol_version=3)
    sync_table(User)
    sync_table(Order)
    sync_table(Stocks)
    sync_table(Payment)
    app.run()
