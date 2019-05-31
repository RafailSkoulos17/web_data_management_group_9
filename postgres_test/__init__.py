import os
# from models import user
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from temp2 import users_api


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleasvlogiaris:amaji5035@5432@localhost/achilleasvlogiaris'
db = SQLAlchemy(app)



