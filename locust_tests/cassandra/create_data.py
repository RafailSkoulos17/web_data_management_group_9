import json
import os
import random
import string
import uuid

VOWELS = "aeiou"
CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))


def generate_word(length):
    word = ""
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word


def create_users(num_users=100):
    if os.path.isfile('dummy_data.json'):
        with open('dummy_data.json', 'r') as f:
            dummy_data = json.load(f)
    else:
        dummy_data = {}

    dummy_data['users'] = []
    for i in range(num_users):
        first_name = generate_word(length=10)
        last_name = generate_word(length=10)
        credit = random.randint(20, 1000)
        email = generate_word(20) + '@' + generate_word(20) + '.com'
        dummy_data['users'] += [[first_name, last_name, email, credit]]
    with open('dummy_data.json', 'w') as f:
        json.dump(dummy_data, f, indent=4, separators=(',', ':'))


def create_stock(num_products):
    if os.path.isfile('dummy_data.json'):
        with open('dummy_data.json', 'r') as f:
            dummy_data = json.load(f)
    else:
        dummy_data = {}
    dummy_data['stock'] = []
    for i in range(num_products):
        product_name = generate_word(10)
        product_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, product_name))
        availability = True
        stock = random.randint(20, 1000)
        price = random.randint(1, 100)
        dummy_data['stock'] += [[product_name, product_id, availability, stock, price]]
    with open('dummy_data.json', 'w') as f:
        json.dump(dummy_data, f, indent=4, separators=(',', ':'))


if __name__ == '__main__':
    create_users(num_users=10000)
    create_stock(num_products=25000)
