## Locust tests of our application

This directory contains all the tests conducted 
for our application for both Cassandra and PostgreSQL.
The test for each of the databases are on the relative subdirectory.

### Procedure

The procedure followed for both databases is the same:
1. We use **create_data.py** to create dummy data which are used for the
creation of the users and the stock.
2. We run a locust task for the creation of the users.
3. We run a locust task for the creation of stock. We create many product
in large quantities so as not to run out of stock when creating the orders.
4. We chose random users from the created ones and we created orders with products 
that exist on stock.
5. Finally, we run a locust task for the checkout of the created orders.

### Performance

**The performance of our application was measured in terms 
of checkouts per second.**