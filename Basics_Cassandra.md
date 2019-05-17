### Introduction to Cassandra

Cassandra : NoSql management system.
No master slave arranegment. Allow masterclass replication across multiple datacenter allowing low latency for all clients.
Based on key-value pairs. Initially developed by facebook.


Cassandra has p2p distributed system across its nodes, and data is distributed among all the nodes in a cluster.
- All nodes are independent
- Any node can accept read and write requests.
- Other nodes serve, when a node is down.

Data Replication in cass - nodes will be replicas for piece of data.
- Perform read repair if data out of date.
- Gossip protocol : Validates whether the data is up-to-date.

Also called data sharding.

Node - It is the place where data is stored. Can be a single server.
Data center - Collection of related nodes.
Cluster - Component that contains 1 or more data centers.
Commit log - crash recovery mechanism in cassandra. Every write operation is written to commit log.
Mem-table - A memory-resident data structure. After commit log, the data will be written to the mem-table. Sometimes, for a single column family, there will be multiple mem-tables.
SSTable(Sorted string table) - It is a disk file to which the data is flushed from the mem-table.

#### Data Model

**Keyspace** - It is the outermost container for data in Cassandra. Similar to schema of RDBS.

- *Replication Factor* : Define in how many nodes the data needs to be replicated.
- *Replica Placement Strategy* : Strategy of how the data needs to be replicated.
- *Column Family* : Similar to a table in RDBMS. Each Keyspace will have multiple column family. It is a container for an ordered collection of rows. Each row, in turn is an ordered collection of columns.

- keys_cached - it represents the number of locations to keep cached per SStable.
- rows_cached - It represents the number of rows whose entire contents will be cached in memory.
- preload_row_cached - It specifies whether you want to pre-populate the row cache.

Column is the basic data structure of Cassandra with three values, namely key or column name, value, and a time stamp.

Supercolumn : Map to multiple keys.

CQLSH : Cassandra query language shell. Using this, you can execute Cassandra Query Language(CQL).

CQLSH Shell commands - help, describe, show, capture, etc.
CQLSH Data commands - create, alter, drop of keyspace, columnfamily, index


Python Flask

Java notes

Find all the Java Virtual Machines installed
/usr/libexec/java_home -verbose

Find path to a version(8)
*/usr/libexec/java_home -v '1.8*'

start cassandra : Go to the folder where cassandra is installed
cassandra -f
open another terminal to start the cassandrs shell query

### Cassandra Query language
cqlsh

CREATE KEYSPACE cassandratraining
WITH replication = {'class':'SimpleStrategy','replication_factor' : 3} //Data is replicated in three nodes.SimpleStrategy is the replica strategy

//Check the keyspace created

DESCRIBE keyspaces;

//Modify keyspace

ALTER KEYSPACE cassandratraining
WITH replication = {'class':'NetworkTopologyStrategy','replication_factor' : 3}

//Delete keyspace

DROP KEYSPACE

//USE keyspace name

USE northwind;

cqlsh:northwind> CREATE TABLE orders(
             ... OrderID int,
             ... CustomerID text,
             ... EmployeeID int,
             ... ShipName text,
             ... ShipCity text,
             ... ShipPostalCode text,
             ... ShipCountry text,
             ... PRIMARY KEY(OrderID)
             ... )

- To check : Types of replica strategies, durable_write

note : Only one node in my laptop but replication factor given is 3.

//Add another column(EmployeeEmail) to the table(orders)
ALTER TABLE orders ADD EmployeeEmail text

//Insert values
INSERT INTO orders(OrderID,CustomerID,EmployeeID,ShipCity) values(1,'0002',234,'Delft')

//check values
select * from orders
