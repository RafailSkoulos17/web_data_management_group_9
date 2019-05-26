from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Stocks(Model):
    __table_name__ = 'stocks'
    __keyspace__ = "stockspace"
    product_id = columns.UUID(primary_key=True)
    product_name = columns.Text()
    stock = columns.BigInt()
    availability = columns.Boolean()

    def get_data(self):
        return {
            'product_id': str(self.product_id),
            'product_name': self.product_name,
            'stock': self.stock,
            'availability': self.availability
        }
