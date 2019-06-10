# to use it install locustio (pip install locustio), run: locust -f locust_users.py
# and connect to http://localhost:8089/ or any other port specified when running locust

import json
from random import randint
from locust import HttpLocust, TaskSet, task
import logging
from locust.contrib.fasthttp import FastHttpLocust
from locust.exception import StopLocust

with open("dummy_data.json", "r") as f:
    dummy_data = json.load(f)

created_ids = {}
with open('created_ids.json', 'r') as f:
    created_ids = json.load(f)
created_ids['user_ids'] = []
dummy_users = dummy_data["users"]


class CreateUsersSteps(TaskSet):

    @task
    def create_user(self):
        if len(dummy_users) > 0:
            self.first_name, self.last_name, self.email, self.credit, = dummy_users.pop()
        else:
            raise StopLocust

        user_create_response = self.client.post("/users/create/", data=json.dumps({
            'email': self.email, 'credit': self.credit, 'first_name': self.first_name, 'last_name': self.last_name
        }), headers={'content-type': 'application/json'}, stream=True)

        if user_create_response:
            if json.loads(user_create_response.content)['success']:
                user_id = json.loads(user_create_response.content)['id']
                created_ids['user_ids'] += [user_id]
                logging.info('Created user %s %s', self.first_name, self.last_name)


class CreateUsersTest(FastHttpLocust):
    task_set = CreateUsersSteps

    host = "http://userLB-1223433602.us-east-2.elb.amazonaws.com"
    sock = None

    # min_wait = 1000
    # max_wait = 1000

    def __init__(self):
        super(CreateUsersTest, self).__init__()

    def teardown(self):
        with open('created_ids.json', 'w') as f:
            json.dump(created_ids, f, indent=4, separators=(',', ':'))
