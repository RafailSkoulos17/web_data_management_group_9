from first import db
from sqlalchemy import Table, Column, Integer, String, MetaData

class Order(db.Model):
    __table_name__ = 'orders'

    user_id = db.Column.UUID()
    order_id = db.Column.UUID(primary_key=True)
    first_name = db.Column.Text()
    last_name = db.Column.Text()
    product = db.Column.Map(key_type=db.column.UUID(), value_type=db.column.Integer(), default={})
    payment_status = db.Column.Boolean()

    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'product': self.product,
            'order_id': str(self.order_id),
            'payment_status': self.payment_status
        }



