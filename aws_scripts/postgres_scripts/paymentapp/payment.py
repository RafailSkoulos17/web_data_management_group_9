from payment_app import db
from sqlalchemy.dialects.postgresql import UUID


class Payment(db.Model):
    __table_name__ = 'payments'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"),nullable = False)
    payment_id = db.Column(UUID(as_uuid=True), primary_key=True)
    status = db.Column(db.Boolean())
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey("orders.order_id"),nullable = False)
    amount = db.Column.Integer()

    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'payment_id': str(self.payment_id),
            'status': self.status,
            'order_id': str(self.order_id),
            'amount': str(self.amount)
        }

    def get_status(self):
        return {
            'status': self.status
        }
