from first import db
import uuid


class Payment(db.Model):
    __table_name__ = 'payments'
    user_id = db.Column.UUID()
    first_name = db.Column.Text()
    last_name = db.Columns.Text()
    email = db.Column.Text()
    payment_id = db.Column.UUID()
    status = db.Column.Boolean()
    order_id = db.Column.UUID(primary_key=True)
    product = db.Column.Text()
    amount = db.Column.Integer()

    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'payment_id': str(self.payment_id),
            'status': self.status,
            'order_id': str(self.order_id),
            'amount': str(self.amount),
            'product': str(self.product)
        }

    def get_status(self):
        return {
            'status': self.status
        }
