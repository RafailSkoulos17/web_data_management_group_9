from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Payment(Model):
    __table_name__ = 'payments'
    __keyspace__ = "paymentspace"
    user_id = columns.UUID()
    first_name = columns.Text()
    last_name = columns.Text()
    email = columns.Text()
    payment_id = columns.UUID()
    status = columns.Boolean()
    order_id = columns.UUID(primary_key=True)
    product = columns.Text()
    amount = columns.Integer()

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
