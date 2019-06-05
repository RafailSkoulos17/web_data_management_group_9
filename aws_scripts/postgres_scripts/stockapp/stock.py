from stock_app import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_views import CreateView, DropView

class Stocks(db.Model):
    __table_name__ = 'stocks'
    product_id = db.Column(UUID(as_uuid=True), primary_key=True)
    product_name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    stock = db.Column(db.Integer)
    availability = db.Column(db.Boolean())

    def __repr__(self):
            return '<Product %r>' % self.product_name

    def get_data(self):
        return {
                'product_id': str(self.product_id),
                'product_name': self.product_name,
                'stock': self.stock,
                'availability': self.availability
               }
