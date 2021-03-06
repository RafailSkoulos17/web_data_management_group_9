# Task to perform the order creation process
# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from random import randint
from locust import HttpLocust, TaskSet, task
# from locust.contrib.fasthttp import FastHttpLocust
from json import JSONDecodeError
import logging

from locust.exception import StopLocust

with open("created_ids.json", "r") as f:
    created_ids = json.load(f)
user_ids = created_ids['user_ids']
product_ids = created_ids['product_ids']
created_ids['order_ids'] = []
n_orders = list(range(30000))


class CreateOrderSteps(TaskSet):

    def on_start(self):
        self.user_id = user_ids[randint(0, len(user_ids) - 1)]
        self.product_id = [product_ids[randint(0, len(product_ids) - 1)] for _ in range(randint(1, 4))]

    @task
    def create_order(self):
        """
        Task to simulate the creation of order for each simulated user
        """
        if len(n_orders) <= 0:
            raise StopLocust
        _ = n_orders.pop()
        product = {pr: randint(1, 4) for pr in self.product_id}
        create_order_respone = self.client.post("/orders/create/{}".format(str(self.user_id)), data=json.dumps({
            'product': product}), headers={'content-type': 'application/json'})
        try:
            if create_order_respone:
                if json.loads(create_order_respone.content)['success']:
                    order_id = json.loads(create_order_respone.content)['order_id']
                    logging.info('Created order with id= %s', str(order_id))
                    created_ids['order_ids'] += [str(order_id)]
                else:
                    logging.info('Failed to create order')
            else:
                logging.info('ERROR_HERE' + json.loads(create_order_respone.content)['message'])
        except JSONDecodeError as jde:
            logging.info('ERROR_HERE' + str(jde.doc))


class CreateOrderTest(HttpLocust):
    task_set = CreateOrderSteps
    host = "http://54.152.228.72:8081"
    sock = None

    def __init__(self):
        super(CreateOrderTest, self).__init__()

    def teardown(self):
        with open('created_ids.json', 'w') as f:
            json.dump(created_ids, f, indent=4, separators=(',', ':'))
