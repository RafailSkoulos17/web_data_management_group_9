#Connect to the local instance of cassandra in your machine
from cassandra.cluster import Cluster
cluster = Cluster()
session = cluster.connect('northwind')
print(session)
#Alter session
session.set_keyspace('northwind')
rows = session.execute('select OrderID,CustomerID,EmployeeID,ShipCity from orders')
for orders in rows:
	print(orders.orderid)

