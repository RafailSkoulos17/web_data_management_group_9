# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from random import randint

from locust import HttpLocust, TaskSet, task
import logging

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)

with open("created_ids.json", "r") as f:
    created_user_ids = json.load(f)
user_ids = created_user_ids['user_ids']
product_ids = created_user_ids['product_ids']
order_ids = created_user_ids['order_ids']


class CheckoutSteps(TaskSet):

    @task
    def checkout(self):
        if len(order_ids) > 0:
            self.order_id = order_ids.pop()
        else:
            exit()
        checkout_reponse = self.client.post("/orders/checkout/{}".format(str(self.order_id)),
                                            headers={'content-type': 'application/json'})
        if checkout_reponse:
            if json.loads(checkout_reponse.content)['success']:
                logging.info('Successful checkout for order with id= %s', self.order_id)
            else:
                logging.info(json.loads(checkout_reponse.content)['message'])
        #     else:
        #         logging.info('Checkout failed for order with id= %s', self.order_id)
        # else:
        #     logging.info('Checkout failed for order with id= %s', self.order_id)


class CheckoutTest(HttpLocust):
    task_set = CheckoutSteps
    host = "http://54.147.93.170:8081"
    # host = "http://127.0.0.1:5000"
    sock = None

    def __init__(self):
        super(CheckoutTest, self).__init__()