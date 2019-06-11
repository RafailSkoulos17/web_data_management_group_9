## Cassandra scripts used

This directory contains all the scripts used to deploy the application
servers for cassandra. Each subdirectory contains the scripts related to 
each service with the structure in each subdirectory being the following:

1. app.py -> the main functionalities for the flask application
2. util.py -> needed utils for the application scripts to run
3. models -> the column family model created for each service

The rest files are related to the deployment of the application to AWS 
using Flask, Nginx and Gunicorn and their functionality is the following

1. app_config -> the Nginx configuration to bind certain ports of the server
to the Nginx http proxy and subsequently to unix sockets
2. {service_name}.service -> the Gunicorn service files
3. flask_application_setup -> simple initial steps to deploy a flask application to AWS using Nginx and Gunicorn
