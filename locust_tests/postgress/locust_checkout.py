# Performs the checkout process
# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from locust import HttpLocust, TaskSet, task
# from locust.contrib.fasthttp import FastHttpLocust
import logging
from locust.exception import StopLocust
from json import JSONDecodeError


with open("created_ids.json", "r") as f:
    created_user_ids = json.load(f)
user_ids = created_user_ids['user_ids']
product_ids = created_user_ids['product_ids']
order_ids = created_user_ids['order_ids']


class CheckoutSteps(TaskSet):

    @task
    def checkout(self):
        """
        Task to simulate the checkout process for each user.
        """
        if len(order_ids) > 0:
            self.order_id = order_ids.pop()
        else:
            raise StopLocust
        checkout_reponse = self.client.post("/orders/checkout/{}".format(self.order_id),
                                            headers={'content-type': 'application/json'})
        try:
            if checkout_reponse:
                if json.loads(checkout_reponse.content)['success']:
                    logging.info('Successful checkout for order with id= %s', self.order_id)
                else:
                    logging.info('Checkout failed for order with id= %s', self.order_id)
            else:
                logging.info('ERROR_HERE' + json.loads(checkout_reponse.content)['message'])
        except JSONDecodeError as jde:
            logging.info('ERROR_HERE' + str(jde.doc))


class CheckoutTest(HttpLocust):
    task_set = CheckoutSteps
    host = "http://54.152.228.72:8081"
    sock = None

    def __init__(self):
        super(CheckoutTest, self).__init__()
