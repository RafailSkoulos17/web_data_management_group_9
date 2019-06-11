# web_data_management_group_9

This project contains implementation of a set of microservices that need to coordinate to guarantee data consistency.

## Microservices using Cassandra and Postgres

We have created the below mentioned microservices with Cassandra and Postgres db to understand the effect of different technologies to design patterns in data management aspects of microservices.

Microservices Implemented:
1. Users(create,remove,find,update)
2. Orders(create,remove,find,addItem,removeItem,checkout)
3. Stocks(create,find,add,subtract)
4. Payment(Pay,cancel,status)

### Cassandra

Cassandra is a NoSQL distributed database by Apache. It is highly scalable and designed to manage large amounts of structured data.

#### Applications and plugins used

1. Flask : Micro web framework written in python 
2. cqlengine : Cassandra Object mapper for python

### Postgres

Postgres is an RDBMS which uses and extends the SQL language by adding many features that can safely store and scale complicated data workloads.

#### Applications and plugins used

1. Flask : Micro web framework written in python
2. sqlalchemy : Postgresql object mapper for python

### Using AWS

We have used AWS for deploying the services in different EC2 instances and RDS instances. A detailed description has been provided in the 'aws_scripts' folder.
