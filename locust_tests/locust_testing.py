# to use it install locustio (pip install locustio), run: locust -f locust_testing.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from random import randint

from locust import HttpLocust, TaskSet, task
import logging

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)


class CreateUsersSteps(TaskSet):
    def on_start(self):
        self.email, self.credit, self.first_name, self.last_name = dummy_data['users'][
            randint(0, len(dummy_data['users']) - 1)]
        self.product_name, self.product_id, self.availability, self.stock = dummy_data['stock'][
            randint(0, len(dummy_data['stock']) - 1)]

    # @task
    # def home(self):
    #     self.client.get("/")
    #     logging.info('Created user')

    @task
    def create_user(self):
        self.client.post("/users/create/", data=json.dumps({
            'email': self.email, 'credit': self.credit, 'first_name': self.first_name, 'last_name': self.last_name
        }), headers={'content-type': 'application/json'})
        logging.info('Created user %s %s', self.first_name, self.last_name)

    @task
    def create_stock(self):
        create_stock_respone = self.client.post("/stock/item/create/", data=json.dumps({
            'product_name': self.product_name}), headers={'content-type': 'application/json'})
        # logging.info(create_stock_respone.content)
        product_id = json.loads(create_stock_respone.content)['product_id']
        self.client.post("/stock/add/{0}/{1}".format(product_id, self.stock),
                         headers={'content-type': 'application/json'})
        logging.info('Created %s products %s ', self.stock, self.product_name)


class CreateUsersTest(HttpLocust):
    task_set = CreateUsersSteps
    host = "http://3.217.184.15:8083"  # for stock
    # host = "http://3.217.184.15:8080" #for user
    sock = None

    def __init__(self):
        super(CreateUsersTest, self).__init__()
