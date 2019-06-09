# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from random import randint
from locust import HttpLocust, TaskSet, task
from locust.contrib.fasthttp import FastHttpLocust

import logging

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)

created_ids = {}
with open('created_ids.json', 'r') as f:
    created_ids = json.load(f)
created_ids['product_ids'] = []


class CreateStockSteps(TaskSet):

    def on_start(self):
        self.first_name, self.last_name, self.email, self.credit, = dummy_data['users'][
            randint(0, len(dummy_data['users']) - 1)]
        self.product_name, self.product_id, self.availability, self.stock, self.price = dummy_data['stock'][
            randint(0, len(dummy_data['stock']) - 1)]

    @task
    def create_stock(self):
        create_stock_respone = self.client.post("/stock/item/create/", data=json.dumps({
            'product_name': self.product_name, 'price': self.price}), headers={'content-type': 'application/json'})
        stock_add_response = None
        if create_stock_respone:
            if json.loads(create_stock_respone.content)['success']:
                product_id = json.loads(create_stock_respone.content)['product_id']
                stock_add_response = self.client.post("/stock/add/{0}/{1}".format(product_id, self.stock),
                                                      headers={'content-type': 'application/json'})
        if stock_add_response:
            if json.loads(stock_add_response.content)['success']:
                created_ids['product_ids'] += [str(product_id)]
                logging.info('Created %s products %s with id= %s ', self.stock, self.product_name, product_id)


class CreateStockTest(FastHttpLocust):
    task_set = CreateStockSteps
    # user_ip: 18.191.23.53
    # order ip: 18.188.32.79
    # payment ip: 18.223.161.135
    # stock ip: 18.216.96.248

    host = "http://18.216.96.248"

    # host = "http://127.0.0.1:5000"

    def __init__(self):
        super(CreateStockTest, self).__init__()

    def teardown(self):
        with open('created_ids.json', 'w') as f:
            json.dump(created_ids, f, indent=4, separators=(',', ':'))
