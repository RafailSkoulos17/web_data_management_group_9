from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from first import db
import uuid

class User(db.Model):
    __table_name__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=False, unique=True, nullable=False)
    last_name = db.Column(db.String(64), index=False, unique=True, nullable=False)
    credit = db.Column(db.Float(0.0))
    email = db.Column(db.String(64), index=False, unique=True, nullable=False)

    def get_data(self):
        return {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'credit': str(self.credit),
            'email': self.email
        }

    def get_full_name(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name
        }

    def get_credit(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'credit': self.credit
        }

