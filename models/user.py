import uuid
from cassandra.cqlengine import columns
from base import Base


class Person(Base):
    id = columns.UUID(primary_key=True, default=uuid.uuid4())
    first_name = columns.Text()
    last_name = columns.Text()

    def get_data(self):
        return {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name
        }
