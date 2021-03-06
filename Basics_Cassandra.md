#### Introduction to Cassandra

Cassandra : NoSql management system.
No master slave arrangement. Allow masterclass replication across multiple datacenters providing low latency for all clients.
Based on key-value pairs. Initially developed by facebook.


Cassandra has p2p distributed system across its nodes, and data is distributed among all the nodes in a cluster.
- All nodes are independent
- Any node can accept read and write requests.
- Other nodes serve, when a node is down.

Data Replication in Cassandra - nodes will hold replicas for pieces of data.
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
- *Column Family* : Similar to a table in RDBMS. Each Keyspace will have multiple column families. It is a container for an ordered collection of rows. Each row, in turn, is an ordered collection of columns.

- keys_cached - the number of locations to keep cached per SStable.
- rows_cached - the number of rows whose entire contents will be cached in memory.
- preload_row_cached - it specifies whether you want to pre-populate the row cache.

Column is the basic data structure of Cassandra with three values, namely key or column name, value, and a time stamp.

Supercolumn : Map to multiple keys.

CQLSH : Cassandra query language shell. Using this, you can execute Cassandra Query Language(CQL).

CQLSH Shell commands - help, describe, show, capture, etc.
CQLSH Data commands - create, alter, drop of keyspace, columnfamily, index
