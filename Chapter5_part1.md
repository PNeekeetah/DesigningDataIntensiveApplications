# Part 2

- Part 1 discusses what happens when data is stored only on one machine
- We discuss what happens with multiple machines here

- Scalability : can distribute read/ writes across several machines
- fault tolerance / high availability : multiple machines give you redundancy
- latency : multiple users around the world could leverage geographically close machines

## Scaling to Higher loads

- for higher load, just buy better machines ( more RAM, CPU )
- you can join many such parts together under one OS
- this is a shared memory architecture
- cost is not directly proportional : double the memory is typically more than double the price
- twice the processing power typically doesn't mean twice the throughput
- shared memory can have some fault tolerance because it might have hot swappable components, but the machine is available only in one geographic location

- we also have shared-disk, where separate machines with their own CPU and RAM share an array of hard disks via a fast network
- used for some data warehouses

## Shared-nothing architecture

- called horizontal scaling 
- each machine running a DB is called a Node
- no special hardware required
- could distribute machines to multiple geo locations
- can survive the loss of a data centre
- even smaller companies can now leverage muti-region distributed archs

- horizontal scaling requires careful thought
- there are constraints and trade-offs
- horizontal scaling incurs additional complexity and can use less expressive data models
- a single threaded program can perform better than one running on a cluster of 100 CPUs

## Replication versus partitioning

- the most common ways of storing data across several nodes
- replication means storing the same data on different nodes - provides redundancy
- partitioning is splitting a big DB into smaller subsets ( partitions ) / this is also called sharding

## Replication

- replication is keeping the same data across several machines
- can be used to keep data geographically close to users
- to proivde failover mechanisms
- to scale out to multiple machines to handle multiple reads

- ASSUME that data is small enough to fit only on one machine
- if the data doesn't change over time, replication is easy - copy data from one node o all the others
- difficulty lies in replicating data that changes

- 3 replication methods
    - single-leader
    - multi-leader
    - leaderless

- You have to consider sync versus async replication
- how to handle failed replicas

- Mainstream use of replicas has started more recently

## Leaders and Followers

- how do you ensure data arrives on all replicas?
- most common solution is a leader-based replication

Mechanism:
    1. One of the replicas is designated as Master. The Master takes care of writes
    2. Remaining replicas are known as Slaves. They receive data from the master as part of a replication log. Each follower takes the log from the master and updates the local database by applying the writes in the same order
    3. CLlients can issue Reads to both masters and slaves - writes only issued to master.

- Leader based replication can be used in non relational DBs and it can be extended to things other than databases ( kafka, for example)
- Kafka and RabbitMQ use highly available queues

## Sync versus Async replication

- figure on page 176 pdf ( 154 real life book )
- master has to wait for sync replicas to write the data
- master doesn't wait for async replicas to write the data
- Replication is normally fairly fast - only time it slows down is when the system is falling behind , or because a node has failed, or because the system is operating at capacity
- sync replication means that followers have the most up to date data, but if the sync replica doesn't respond, writes have to be blocked

- sync generally means that only one replica is sync and all the others are async
- if sync replica falls behind or is slow, one of the async ones is made sync
- guaranteed you have the same data on at least 2 nodes
- this configuration is sometimes known as semi-synchronous

- leader based replication is sometimes configured to be fully async
- if the leader fails, it's not guaranteed that follower has the most up to date copy
- writes are not guaranteed to be durable
- leader can continue with writes even if all replicas have fallen behind

- async replication is used widely despite weakening durability
- provides advantages for many replicas or geographically distributed replicas

## Setting up new followers

- you sometimes need to increase number of replicas OR replace failed nodes
- how do you ensure a new follower has an accurate copy of the leaders data
- new replicas should ideally be created with 0 downtime

Mechanism:
    1. Take a consistent snapshot of the leader's DB - ideally without locking the DB
    2. copy snapshot over to follower
    3. follower asks leader for all changes since snapshot
    4. after follower has finished reading all changes since snapshot, it has `caught up` . It can now process changes from leader as they happen

- process can be automated or fully manual ( done by a DB admin for example )

## Handling node outages

- any nodes can go down due to several reasons
- how to achieve high availability with leader based replication ? 

## Follower failure - catch-up recovery

- follower knows last transaction which occured from its logs - it can request latest changes from that point onwards from the leader

## Leader failure - failover

- if the leader fails, a follower needs to be promotes, clients need to reconfigure where they send their writes, other followers need to start consuming data from new leader
- failover can happen manually or automatically

Automatic failover mechanism:
    1. Most system use a timeout. If the leader doesn't respond in 30 seconds, it's assumed it's dead
    2. The new leader is elected. Remaining replicas decide who becomes the leader. The most suitable candidate is the replica with the most up to date data. Getting the nodes to agree is a consensus problem
    3. clients now need to send writes to the new leader. If old leader comes back online, it can still believe that it is the leader - it has to be forced to step down 

Failover has many issues
    1. In async replication, it's not guaranteed that the new leader had the latest writes from the leader that went down. What do you do with those writes? Most commonly, those writes are discarded.
    2. Discarding items is dangerous if another system outside of the database needs to be coordinated with the DB contents - An out of date MYSQL follower was promoted to leader in Github - there was an auto-incrementing counter which assigned primary keys to new rows, there was also a Redis store which stored the keys and this led to some users being able to access data from other users
    3. Two nodes can believe they are the leader - this leads to a `split-brain` situation. Strategies to shut down one of the leaders have to be designed carefully, else you risk shutting down both ( https://en.wikipedia.org/wiki/STONITH)
    4. What is the right timeout before you consider the old leader `dead` ? Longer timeouts means more time to recover, but shorter times mean more fail-over overhead. Unecessary fail-overs can make the situation of a struggling system worse

- Some teams prefer to do failovers manually
- unreliable networks, tradeoffs around replica consistemncy, durability, availability and latency are fundamental problems to ditributed systems

## Implementation of Replication Logs
### Statement based replication

- for relational DBs, the leader has to send all INSERT, UPDATE and DELETE statements
- followers get the sql statements as if they have been received from the client 
- This form of replication can break down due to things like
  - using NOW() or RAND() statements ( replicas will generate their own timestamps / random numbers) 
  - if statements use an auto-incrementing column, the statements must be executed in the same order
  - statements can have side effects - IDEALLY they are deterministic

- TO SOLVE THIS, the leader can replace `NOW()` with the result of having called the function
- there are many other edge cases
- statement based replication is still used sometimes today
- VoltDB uses statemnt based replication and makes it safe by requiring transactions to be deterministic

### Write ahead log shipping

- chapter 3 noted that each write is typically appended to a log
- the log is an append only sequence of bytes containing all writes - the log can be used to build an exact replica on another node
- besides writing the log to disk, this is also sent to followers
- this method is used by Postgres and Oracle
- replication is closely coupled to the storage engine
- CANNOT RUN different DB versions on  followers and leaders
- This typically means that it is hard to upgrade the version (which means downtime)
- If one of the replicas can have a newer version, then all replicas are updated first, otherwise, you have to shut down everything

### Logical (row-based) replication

- can use different log formats for replication
- this is a logical log
- this is a sequence of records describing writes to the DB at the granularity of a row
- for a written row, the log contains the values for all columns
- for a deleted row, sufficient information to determine the column ( e.g. the primary key)
- for an updated row, enough info to uniquely identify the column + the new data

- MY SQL uses this approach
- logical logs are more easily kept backwards compatible, which means that leaders and followers can run on different versions
- logical logs are easier for external applications to parse (e.g. to data warehouses)

### Trigger based replication

- sometimes, you want to replicate only a subset of the data or you need some conflict resolution logic
- replication needs to move up the application layer
- can use triggers and stored procedures
- Triggers let you register custom application code that is automatically executed on data changes
- trigger based replication has more overhead

## Problems with replication lag

- handling node failures is just one reason
- the other reaasons are scalability and latency
- web apps typically require many reads and not a lot of writes - this makes replication attractive since reads can be off-loaded to replicas
- can increase capacity for serving reads by adding more followers
- NOTE : ONLY WORKS WITH ASYNC FOLLOWERS

- If an app reads from async nodes, they have likely fallen behind - leads to apparent inconsistencies
- the inconsistency is a te,mporary state - all followers eventually catch up, which leads to `eventual consistency`
- `eventually` is used as a handwavy term - it doesn't usually prescribe how long it takes
- for a system at capacity, the lag can increase to seconds or minutes

Approaches for solving this

### Read your own writes

- User writes data to a the DB leader, and then reads from a replica - data might not have been written there, so it appears as if the change has not been registered (page 163 - 185 pdf)#
- We need read-after-write consistency (or read your writes consistency)

- When user writes something, read the user's written data from leader. For other users, read from replicas - works well with social media
- if a lot of things can be changed by the user (e.g. outside of own profile ),  this doesn't work well / you could use a time based mechanism where you serve read requests from the last minute from the leader, and the rest from replicas
- the client can remember the timestamp of the most recent write - the system can ensure that a replica whose timestamp matches most closely the client's serves the request ( `unreliable clocks` are an issue here)
- for multiple datacentres, this becomes an issue because you will have to reroute to the datacentre with the leader

- The user might hold multiple devices, and these devices all have to see the latest data written by this user
- more issues need to be considered -the clients cannot remember the user's latest timestamp since this is all scattered across devices
- request for the user's devices have to be routed to the same datacentre - the devices could live on different networks

### Monotonic reads

- the user can see things moving backwards in time if there are multiple async replicas
- Figure from page 187 ( 165 ) 
- happens when reads are served from random replicas
- ensure that data is read from the same repklica for each user

### Consistent prefix reads

- writes which happen in a certain order will be seen IN THAT ORDER when read by anybody ( page 188 pdf, page 166 real book)
- in many distributed databases, different partitions operate independely / no global ordering of wirtes
- maintain writes that are closesly related to each otther in opne partition 
- algos keep track of casual dependencies

## Solutions for replication lag

- how does the system behave if the replication lag increases to several minutes ? 
- there are ways to provide a stronger guarantees 
- ideally, you want to trust that your DBs will do the right thing (otherwise, developer code becomes more complex)
- reason why transactions exist
