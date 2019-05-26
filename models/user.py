from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class User(Model):
    __table_name__ = 'users'
    __keyspace__ = "userspace"
    # id = columns.UUID(primary_key=True, default=uuid.uuid4()) # maybe to be used later
    id = columns.UUID(primary_key=True)
    first_name = columns.Text()
    last_name = columns.Text()
    credit = columns.Float(default=0.0)
    email = columns.Text()

    def get_data(self):
        return {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'credit': str(self.credit),
            'email': self.email
        }

    def get_full_name(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name
        }

    def get_credit(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'credit': self.credit
        }
