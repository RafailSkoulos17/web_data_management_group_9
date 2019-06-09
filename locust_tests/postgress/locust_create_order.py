# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
import uuid
from random import randint
from locust import HttpLocust, TaskSet, task
from locust.contrib.fasthttp import FastHttpLocust

import logging

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)

with open("created_ids.json", "r") as f:
    created_ids = json.load(f)
user_ids = created_ids['user_ids']
product_ids = created_ids['product_ids']
created_ids['order_ids'] = []


class CreateOrderSteps(TaskSet):

    def on_start(self):
        self.user_id = user_ids[randint(0, len(user_ids)-1)]
        self.product_id = [product_ids[randint(0, len(product_ids)-1)] for _ in range(randint(1, 4))]

    @task
    def create_order(self):
        product = {pr: randint(1, 4) for pr in self.product_id}
        create_order_respone = self.client.post("/orders/create/{}".format(str(self.user_id)), data=json.dumps({
            'product': product}), headers={'content-type': 'application/json'})
        if create_order_respone:
            if json.loads(create_order_respone.content)['success']:
                # logging.info('Order is= %s', json.loads(create_order_respone.content))
                order_id = json.loads(create_order_respone.content)['order_id']
                logging.info('Created order with id= %s', str(order_id))
                created_ids['order_ids'] += [str(order_id)]
            else:
                logging.info('Failed to create order')
        else:
            logging.info('Failed to create order')


class CreateOrderTest(FastHttpLocust):
    task_set = CreateOrderSteps
    host = "http://3.91.13.122:8081"

    # host = "http://127.0.0.1:5000"
    sock = None

    def __init__(self):
        super(CreateOrderTest, self).__init__()

    def teardown(self):
        with open('created_ids.json', 'w') as f:
            json.dump(created_ids, f, indent=4, separators=(',', ':'))
