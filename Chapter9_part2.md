### Using total order broadcast

- Zookeeper and etcd both implement TOB ( connection between TOB and consensus )
- replicas process writes in the same order && replicas remain consistent - TOB is what you need
- this is known as state machine replication
- TOB can be used to implement serializable transactions
- transactions cannot be inserted at an earlier point in time (i.e. before another transaction) when TOB is used - this is stronger than timestamp ordering
- TOB is also like a log (WAL)
- TOB can be used to implement fencing tokens 

### Implementing linearizable storage with TOB

- TOB is used to implement linearizability, but they're not the same
- TOB guarantees that the order is the same - Linearizability is a recency guarantee
- TOB helps with the username uniqueness problem 
- Implement a Linearizable compare and set operation as follows :
    1. Append message to log with username you want to claim
    2. read the log and wait for your message to be delivered back
    3. check all messages claiming the username you want - if yours is the first, append a commit to your log

- You discard all later conflicting writes
- Linearizable writes are ensured like this - reads are not ( i.e. because you might read stale data )
- It ensures Timeline consistency though
- For linearizable reads, you can:
    1. append a message in the log and perform the read when the message is delivered back
    2. if you can fetch the position of the last log in a linearizable way, wait for all messages to be read up until there and read only when you reach the last message
    3. read from a replica which is synchronously updated on writes ( used in chain replication )

### Implementing TOB using linearizable storage

- previous section was the reverse of this
- easiest linearizable register stores an int and has an atomic increment and get operation
- atomic CAS could also do the job
- For every message you send, you do an IncAndGet and send the message with the integer - you send these to all nodes (and attempt to redeliver if failed ) and recipients will deliver the messages by sequence number
- Unlike Lamport timestamps, the number from IncAndGet doesn't have any gaps ( you know you have to wait for 5 if you have only 4 and 6)
- Key difference between TOB and timestamp ordering
- For a single replica, this is easy - for multiple replicas, you get a consensus problem
- linearizable IncrementAndGet and TOB are both equivalent to consensus

## Distributed Transactions and Consensus

- consensus is a hard problem
- requires knowledge about replication, transactions, linearizability and TOB
- situations where consensus is important
    1. leader election (e.g. when a network problem occurs and a new leader is elected)
    2. atomic commit (transactions which span multiple nodes/ partitions - may fail on some, may succeed on others - roll back or commit? atomic commit problem)

- FLP result - consensus is impossible to be achieved by any algorithm if nodes may crash
- FLP proved this for the asynchronous model - if timeouts are used, consensus becomes a solveable problem
- in practice, consensus is achievable

- 2PC  (2 phase commit) is a kind of consensus algorithm - but not a very good one
- Zookeeper uses Zab and etcd uses Raft
- we will first study the atomic commit problem

### Atomic commit and two phase commit (2PC)

- transaction atomicity is there for us to be able to easily reason about what we do with failed transactions
- prevents half finished transactions from kicking about - especially important for Multi object transactions and Secondary Indexes
- if you don't update your secondary indexes, they're not really useful 

### From single node to distributed atomic commit 

- atomicity for transactions is implemented by the storage engine on a single database node
- you can use a WAL. if the node crashes, look for the COMMIT. If `COMMIT`ed, re-execute the transaction - else, rollback
- transaction commitment on a single node depends on whether data was durably written to the disk AND whether the COMMIT record exists
- for multiple nodes, things become hairy
- Most NoSql don't support multi object transactions on different nodes - various clusters of relational databases support it though
- you cannot commit separately on all nodes - the commit might fail on some and it might succeed on other
- if some commit and others rollback, the database becomes inconsistent
- transactions cannot be revoked once commited
- if other transactions base their changes around the result of the revoked transaction, those need to get reverted as well
- ( the effects of a transaction can later be undone by a compensating transaction )

### Intro to 2PC

- algorithm to ensure that a transaction executed on multiple nodes EITHER commits or aborts properly
- rather than a single commit request, 2PC has 2 phases:
- Refer to figure 9-9 on page 356 (page 378 on the PDF version)
- 2PC is different from 2PL - 2PL provides serializable isolation, 2PC provides atomic commits in a distributed DB
- NOTHING IN COMMON between these 2

- 2PC uses a coordinator ( or a transaction manager )
- Reads and writes occur as normal - nodes are called participants in the transaction
- When the application is ready to commit, the coordinator sends a prepare request to each node 
    -> if all respond yes, send commit request
    -> if all respond no, send rollback request

- It's just like marriage!

### A system of promises

- this explains why 2PC works

1. when the app wants a distributed transaction, it requests a unique TX id
2. a single node TX is started on all nodes with the unique TX id
3. when ready to commit, the coordinator sends a prepare request with the TX id to all participants
4. participants may NOT abort the TX once they respond to the prepare request with yes (crashes, power failures, running out of disk space are not acceptable)
5. coordinator writes to disk its transaction
log (in case of a crash) - this is the commit point
6. Once the decision is written to disk, the commit/abort request is sent to all participants

- Once we've reached 6, there will be as many retries as necessary until the commit is fulfilled
- There are two points of no return:
    - when a participant votes yes
    - when the coordinator decides to go forth

- more marriage analogies here which are hilarious (e.g. what if you faint ? )

### Coordinator failure

- it's clear what happens when participants crash - less so when the coordinator fails
- if the coordinator fails and the participant is still waiting for the response, the transaction's state is called in doubt
- refer to figure 9-10 on page 359 (380 on PDF version)
- participants can communicate amongst themselves, but this is not part of 2PC
- We wait for the coordinator to recover 

### Three phase commit

- 2PC is called blocking atomic commit because it can get stuck waiting for the coordinator
- we can make this non-blocking (theoretically)
- 3PC is proposed as an alternative, but it assumes a network with bounded delays and nodes with bounded response times
- nonblocking atomic commits require a perfect failure detector ( i.e. being able to reliably tell whether a node failed or not )
- 2PC continues to be used

## Distributed transactions in practice

- distributed transactions (especially those with 2PC) have a mixed reputation
- they provide a safety guarantee, BUT they bring a considerable performance overhead
- cloud services don't implement these
- Distributed transactions in MySQL are reported to be 10X slower than single node transactions
- the performance cost is because of the disk forcing for crash reovery adn network round trips
- 2 types of distributed transactions
    1. Databse internal distributed transactions - VoltDb, MySQL Cluster's NDB storage engine have such an internal transaction support. all nodes are running the same db software
    2. Heterogeneous distributed transactions - participants have different DBs on them 

- Database internal transactions don't have to be compatible with any other system 
- optimizations for that particular technology can be applied
- Heterogeneous distributed transactions are more challenging

### Exactly once message processing

( I don't actually understand this one )
- a message from a queue is said to be processed IFF the db transaction processing the message succesfully commited
- with distributed transaction support, this is possible even if the message broker are 2 unrelated technologies running on different machines
- if message delivery fails or db transaction fails, bnoth are aborted and the message broker can safely re-deliver / atomically commiting the message
- and the side effects of its porcesing esnures the message is processed only once

### XA Transaction

- eXtended Architecture - standard for implementing 2PC across heterogeneous technologies
- Many relational DBs support XA ( PostgresQL, MYSQL, ORacle) as well as Message Brokers (ActiveMQ, MSMQ, IBM MQ)
- XA is a C API for interfacing with a transaction coordinator
- bindings for the API exist in other languages - in JAVA, XA Transactions are implemeted using JTA 
- it's supported by drivers for DBs using Java Database Connectivity (JDBC) and Java Message Service (JMS)
- XA assumes the aplication uses a network driver or client library to communicate with participant DBS
- ( a lot of other details about XA which I don't really understand )

### Holding locks while in Doubt

- DBs take locks on objects in the database to prevent dirty reads/writes
- You cannot release those locks to other applications whilst you wait to commit your transaction
- if the coordinator crashes for 20 minutes, the locks are held for 20 minutes - if forever, the locks are kept forever
- depending on the implementation, other transactions might be prevented from reading those rows.
- large parts of the application can become blocked until the nodes in doubt are resolved

### Recovering from coordinator failure

- You keep a hold of those locks regardless - even if you restart the nodes or the coordinator
- admins need to decide manually - sticky situation !
- manual resolution requires a lot of effort ( and likely needs to be done under time pressure )
- XA has `heuristic decisions` - probably breaks atomicity, but allows recovery
- not designed for regular use

### Limitations of distributed transactions

- the coordinator is a database is as well
- coordinator is not fault tolerant if not replicated
- coordinator needs to make durable writes
- it doesn't work with SSI
- database internal distributed transactions can  work with SSI
- distributed transactions amplify failures

### Fault tolerant consensus

- consensus aims to answer the question `which of these mutually incompatible operations should be the winner`
- one or more nodes proposes a value - the consensus algorithm decides which value should be selected
- 4 requirements
    1. uniform agreement
    2. integrity (no node votes twice)
    3. validity ( answer is within proposed solutions )
    4. termination (nodes decide on a value)

- 1 and 2 define the core ideas of consensus
- 3 rules out trivial properties
- you can hard code a dictator node if you don't care about 4
- 4 says that your system cannot be idle forever - it must reach a decision
- first 3 are safety properties, the last one is a liveness property
- system model of consensus assumes that if a node `crashes`, it becomes unavailable forever
- there is a number of crashes which a system can support - you need a quorum
- most implementations of consensus implement 1-3  / not all might implement termination
- consensus doesn't traditionally offer protections against Byzantine faults (although it can)

### Consensus algorithms and TOB

- best known fault tolerant consensus algorithms are Raft, ZAB, Paxos and Viewstamped Replication
- These decide on a sequence of values (they are TOB algorithms)
- All except Paxos implement TOB ( more efficient to achieve consensus on multiple values at the same time) - optimization for Paxos is MultiPaxos

### Single Leader Replication and Consensus

- consensus can be achieved by delegating it to humans
- if humans decide which node becomes the leader, the algorithm doesn't satisfy the termination property
- consensus is TOB, and TOB is like single leader AND single leader replication requires a leader -> to elect a leader, you need a leader !

### Epoch numbering and quorums

- all consensus algos use a leader, but the leader is not unique - instead, they guarantee that within an epoch, the leader is unique
- when a leader dies, a new epoch is created where nodes vote on a new leader - if the other node wasn't dead, the leader with the higher epoch prevails
- nodes must collect votes from a quorum - it must receive a majority
- 2 rounds of voting - choosing a leader and choosing the leader's proposal
- looks like 2PC, but isn't (2PC requires all, this requires a majority)
- consensus has a revovery method - nodes can get into a consistent state after a leader is elected

### Limitations of consensus

- many advantages, but they come at a cost
- voting on proposals is like sync replication / most dbs use async replication
- consensus requires a strict majority 
- only the majority makes progress whilst other nodes recover from failures
- consensus algorithms assume a fixed number of nodes that take part in voting (Dynamic membership algorithms exist, but are hard)
- consensus algorithms rely on timeouts to detect failed nodes - in geographically distributed systems, these timeouts are frequent
- can result in terrible performance because more time is spent electing leaders than working
- Consensus algos are sensitive to network problems - `Raft` has edge cases (leadership bounces between 2 nodes)
- designing more robust consensus algoritms in the presence of netowrk faults is still an open research topic

### Membership and coordination services

