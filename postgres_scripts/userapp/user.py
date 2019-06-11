from user_app import db
from sqlalchemy.dialects.postgresql import UUID


class User(db.Model):
    #Define user table
    __table_name__ = 'user'
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    first_name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    last_name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    credit = db.Column(db.Float(0.0))
    email = db.Column(db.String(64), index=False,unique=True, nullable=False)

    #Define all the views
    def __repr__(self):
        return '<User %r>' % self.first_name

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
