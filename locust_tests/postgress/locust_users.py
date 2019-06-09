# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from random import randint
from locust import HttpLocust, TaskSet, task
import logging

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)

created_ids = {}
with open('created_ids.json', 'r') as f:
    created_ids = json.load(f)
created_ids['user_ids'] = []


class CreateUsersSteps(TaskSet):

    def on_start(self):
        self.first_name, self.last_name, self.email, self.credit, = dummy_data['users'][
            randint(0, len(dummy_data['users']) - 1)]
        self.product_name, self.product_id, self.availability, self.stock, self.price = dummy_data['stock'][
            randint(0, len(dummy_data['stock']) - 1)]

    @task
    def create_user(self):
        user_create_response = self.client.post("/users/create/", data=json.dumps({
            'email': self.email, 'credit': self.credit, 'first_name': self.first_name, 'last_name': self.last_name
        }), headers={'content-type': 'application/json'})
        if user_create_response:
            if json.loads(user_create_response.content)['success']:
                user_id = json.loads(user_create_response.content)['id']
                created_ids['user_ids'] += [user_id]
                logging.info('Created user %s %s', self.first_name, self.last_name)
            else:
                print(json.loads(user_create_response.content)['message'])


class CreateUsersTest(HttpLocust):
    task_set = CreateUsersSteps

    host = "http://54.147.93.170:8080"
    # host = "http://127.0.0.1:5000"
    sock = None

    def __init__(self):
        super(CreateUsersTest, self).__init__()

    def teardown(self):
        with open('created_ids.json', 'w') as f:
            json.dump(created_ids, f, indent=4, separators=(',', ':'))
