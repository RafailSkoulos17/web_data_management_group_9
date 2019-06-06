from order_app import db
from sqlalchemy.dialects.postgresql import UUID

class Order(db.Model):
    __table_name__ = 'orders'

    user_id = db.Column(UUID(as_uuid=True),nullable = False)
    order_id = db.Column(UUID(as_uuid=True), primary_key=True)
    items = db.Column(db.JSON())
    payment_status = db.Column(db.Boolean())
    amount = db.Column(db.Float(0.0))

    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'order_id': str(self.order_id),
            'items': str(self.items),
            'amount': str(self.amount),
            'payment_status': str(self.payment_status)
        }



