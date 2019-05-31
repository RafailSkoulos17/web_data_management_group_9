from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from first import db
from models.user import User

# See important note below


db.create_all()
# db.session.commit()

admin = User(id=6, first_name='achilleas', last_name='vlogiaris', credit=54, email='achilleasvlogiaris@gmail.com')
db.session.add(admin)
db.session.commit()
users = User.query.all()
print(users)