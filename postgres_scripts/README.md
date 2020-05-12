## Postgres deployment


 We used 4 VPCs in 4 different availability zones, one VPC per microservice.
 We used 4 different Postgres RDS databsases, one RDS database per service.
 For each VPC, we used as Web server the Nginx and the Gunicorn as WSGI HTTP server (reverse proxy).
 As microframework, the python flask was used, extended with the SQLAlchemy toolkit


### Prerequisites

 Packages that should be installed.
 *psycopg2* and *Flask-SQLAlchemy*


