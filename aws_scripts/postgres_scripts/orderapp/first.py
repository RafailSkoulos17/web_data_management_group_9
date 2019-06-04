from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.debug = True
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Boni1_21101992@localhost/postgres'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleasvlogiaris:amaji5035@5432@localhost/achilleasvlogiaris'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://achilleas:12345678@database-1.cskyofsyxiuk.us-east-1.rds.amazonaws.com:5432/achilleasvlogiaris'
db = SQLAlchemy(app)