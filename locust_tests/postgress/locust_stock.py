# Performs the user creation process
# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from json import JSONDecodeError
from locust import HttpLocust, TaskSet, task
# from locust.contrib.fasthttp import FastHttpLocust
from locust.exception import StopLocust
import logging

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)

with open('created_ids.json', 'r') as f:
    created_ids = json.load(f)
created_ids['product_ids'] = []
dummy_stock = dummy_data["stock"]


class CreateStockSteps(TaskSet):

    @task
    def create_stock(self):
        """
        Task to simulate the creation of a product in stock
        """
        if len(dummy_stock) > 0:
            self.product_name, self.product_id, self.availability, self.stock, self.price = dummy_stock.pop()
        else:
            raise StopLocust

        create_stock_respone = self.client.post("/stock/item/create/", data=json.dumps({
            'product_name': self.product_name, 'price': self.price}), headers={'content-type': 'application/json'})

        stock_add_response = None
        try:
            if create_stock_respone:
                if json.loads(create_stock_respone.content)['success']:
                    product_id = json.loads(create_stock_respone.content)['product_id']
                    stock_add_response = self.client.post("/stock/add/{0}/{1}".format(product_id, self.stock),
                                                          headers={'content-type': 'application/json'})
                    logging.info('%s added to stock', product_id)

                else:
                    logging.info('Failed to add to stock')
            else:
                logging.info('ERROR_HERE' + json.loads(create_stock_respone.content)['message'])
        except JSONDecodeError as jde:
            logging.info('ERROR_HERE' + str(jde.doc))

        try:
            if stock_add_response:
                if json.loads(stock_add_response.content)['success']:
                    created_ids['product_ids'] += [str(product_id)]
                    logging.info('Created %s products %s with id= %s ', self.stock, self.product_name, product_id)
                else:
                    logging.info('Failed to add products with product id= %s', product_id)
            else:
                logging.info('ERROR_HERE' + json.loads(create_stock_respone.content)['message'])
        except JSONDecodeError as jde:
            logging.info('ERROR_HERE' + str(jde.doc))


class CreateStockTest(HttpLocust):
    task_set = CreateStockSteps

    host = "http://54.164.73.11:8083"

    def __init__(self):
        super(CreateStockTest, self).__init__()

    def teardown(self):
        with open('created_ids.json', 'w') as f:
            json.dump(created_ids, f, indent=4, separators=(',', ':'))
