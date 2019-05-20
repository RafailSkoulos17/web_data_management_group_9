import uuid
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Order(Model):
    __table_name__ = 'orders'
    __keyspace__ = "orderspace"
    user_id = columns.UUID()
    order_id = columns.UUID(primary_key=True)
    first_name = columns.Text()
    last_name = columns.Text()
    product = columns.Text()
    amount = columns.Integer()

    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'product': self.product,
            'amount': self.amount,
            'order_id': str(self.order_id)
        }
