from first import db
import uuid

class Stocks(db.Model):
    __table_name__ = 'stocks'
    product_id = db.Column.UUID(primary_key=True)
    product_name = db.Column.Text()
    stock = db.Column.BigInt()
    availability = db.Column.Boolean()

    def get_data(self):
        return {
            'product_id': str(self.product_id),
            'product_name': self.product_name,
            'stock': self.stock,
            'availability': self.availability
        }
