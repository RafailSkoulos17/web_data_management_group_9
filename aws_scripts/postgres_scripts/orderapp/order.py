from order_app import db
from sqlalchemy.dialects.postgresql import UUID

class Order(db.Model):
    __table_name__ = 'orders'

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"),nullable = False)
    order_id = db.Column(UUID(as_uuid=True), primary_key=True)
    product = db.Column(UUID(as_uuid=True), db.ForeignKey("stocks.product_id"),nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    payment_status = db.Column(db.Boolean())

    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'order_id': str(self.order_id),
            'product': str(self.product),
            'quantity': str(self.quantity),
            'payment_status': str(self.payment_status)
        }



