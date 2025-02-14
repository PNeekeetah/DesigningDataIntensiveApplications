# Transactions

- Many issues can occur in data systems
  1. Database Hardware/ software failure
  2. The app may crash 
  3. network interruptions cutting off db-app or db-node from db-node
  4. several writes at the same time
  5. clients may read partial updates
  6. race conditions

 - These are all hard to account for. This is why `transactions` exist.
 - Transactions are a way to group all reads and writes under one single unit - either all succeed ( commit ) or one of them fail ( abort/rollback - THESE MEAN THE SAME in this case )
 - Aborting is better than dealing with partial failures
 - Using transactions makes allows the app to ignore certain error scenarios
 - `transactional guarantees` can be weakened to achieve higher performance/availability
 - everything here applies to both single node and distributed DBs

## The Slippery Concept of a Transaction

- transactions have been around since 1975 and they haven't changed much
- Nonrelational databases weakened the guarantees offered by transactions
- 2 extremes: No large datasystem should use transactions <---> Every serious business application should use transactions

## The Meaning of ACID

- ACID implementations across several databases aren't equal
- ACID stands for Atomicity, Consistency, Isolation and Durability
- If the system doesn't meet ACID criteria, it's called BASE and it's even more loosely defined
- (Basically Available, Soft State, Eventually consistent)

### Atomicity

- This term is conflated - think of atomicity in the context of multi threadding
- If errors occur halfway, they can be safely aborted (and then retried) - it would have been more suitable to call this "Abortability"

### Consistency

- Another conflated term  
- Consistency means that you have statements about your data that are always true
- Is typically a property of the application, not of the database - it was added only to make the acronym work
- You can use atomicity and isolation to achieve consistency, but it relies on the application as well

### Isolation

- accessing the same data can read to race conditions
- page 226 figure 7-1 (248 in digital version)
- Every transaction can pretend that it is the only one currently being run - the result will be the same as if transactions have run serially ( even though they might have run concurrently )
- Serializable isolation is rarely used because of performance implications
- Oracle has an isolation level called `serializable`, but in fact it is talking about `snapshot isolation`, a weaker isolation level

### Durability

- Durability means that once data was written, it will be stored even if a hardware failure occurs
- In single node, it means that it was written to a Nonvolatile storage (SSD/ HDD) and writing to WALs or similar
- In replicated DBs, durability means that the data was copied on another node  ( transactions must wait for data to be copied elsewhere )
- If all your DB nodes go down, you're out of luck
- The meaning of Durability evolved from archiving to disk to replication data across nodes, but nothing is perfect
  1. If the machine where the data is written dies, the hard disk needs to be extracted elsewhere before the data is accessible again
  2. disks can gradually become corrupted
  3. async nodes might be promoted to leaders and data might be lost
  4. when SSDs are disconnected, they can start losing data within a few weeks  

### Single-object and Multi-object operations

- Atomicity provides `all or nothing` guarantees
- Isolation means that if a transaction makes several writes, another transactions either sees all writes or none
- One transaction reading another transaction's uncommited write is called a `dirty read`
- multi object transactions require a way to tell which read and which write belongs to the same transaction
- nonrelational DBs don't have such ways of grouping operations together

### Single-object writes

- Example with a 20KBs JSON write which fails halfway - what happens with the data? Is the old and new data spliced together ? Does the database store the other 10KBs which are corrupted ? 
- Storage engines aim to provide atomicity and isolation on single objects
- Atomicity can be implemented with a log for crash recovery
- Isolation can be implemented with row level locks
- Single object ops are useful, but they are not transactions in the traditional sense of the term

### Multi object writes

- hard to implement in distributed datasystems across several partitions
- can get in the way of performance or high availability when required
- writes need to be coordinated because
    1. data becomes nonsensical if foreign keys get messed up
    2. non relational databases encourage denormalization, but you can end up with wacky results if you have 2 documents referencing the same denormalized field (and that field contains different data)

- applications can be implemented without transactions, but error handling becomes a pain 

### Handling errors and aborts

- transactions can be safely aborted if an error occurs halfway through - it's better to abandon the write altogether
- leaderless replication works on a `best effort` basis - operations won't get undone in this case
- Django and Rails's ActiveRecord don't retry transactions, prefering to bubble an error up the stack (could be retried!)
- Retrying transactions is not a silver bullet 
  1. can lead to dupes if TX (the transaction) succeeded, but the error occured afterwards
  2. if TX failed and the system is overloaded, it will make matters worse
  3. Worth retrying only for transient errors - no reason to try if a constraint violation occured
  4. Side effects will still happen even if transaction was aborted

## Weak isolation levels

- 2 TXs that don't touch the same data can be run in parallel
- concurrency errors touching the same object are hard to reproduce
- weaker isolation levels are used in practice since serializable isolation is costly in practice
- can introduce subtle bugs ( which lead to loss of money, customer data etc)
- ACID databases can use weak isolation! 

### Read commited

- most basic level
- you only see data that has been commited and you only overwrite data that has been commited
- (no dirty reads and no dirty writes)

#### No dirty reads

- If another transaction can see the partial result of another transaction, that is a dirty read
- See figure 7-4 on page 234 ( page 256 on digital version)
- Dirty reads can confuse users if they see the DB in a partially updated state AND it can mess up other transactions if the data gets rolled back

#### No dirty writes

- delay the second transaction's write up until the first transaction has completed
- read commited avoids situations such as Figure 7-5 on page 236 (259 on digital version)
- read commited doesn't prevent race conditions

### Implementing read commited

- read commited is very popular ( PostgreSQL, Oracle, SQL Server 2012 etc use it)
- databases prevent dirty writes by acquiring row level locks for all rows
- could use read locks as well, but you've got problems if you've got a long running transaction
- Rather than using read level locks, databases store values before TX occured and after TX occured

### Snapshot isolation and repeatable read

- Read commited might seem like it provides the Atomicity and Isolation you need, but it doesn't
- `Read skew` (or `nonrepeatable read`) can occur (this is demonstrated in Figure 7-6 on page 237 or 259 in the digital version)
- such inconsistencies are ok in some situations, but backups cannot tolerates them (since restoring such a backup results in permanent money loss in the case of Figure 7-6)
- Snapshot isolation is a common solution to this problem
- Every transaction reads from a consistent snapshot of the database i.e. the transaction sees only the data BEFORE it started executing
- Snapshot isolation is a popular feature ( PostgreSQL, Oracle, MYSQL all implement it)

### Implementing snapshot isolation

- like read commited, you use write locks
- reads do not require locks ( writers shouldn't block readers and vice-versa)
- The database stores multiple commited versions of an object 0 this is called multi version concurrency control (MVCC)
- Figure 7-7 on page 240 (262 digital) shows how Postgres implements MVCC based snapshot isolation

### Visibility rules for a consistent snapshot

1. At the start of a transaction, check all incomplete transactions - ignore all writes
2. Ignore all writes of aborted TXs
3. TXs with a latest TXID are ignored, regardless of commit status
4. All other writes are visible to the app's queries

An object is visible IFF

1. When the reader's transaction started, TX which created the object commited
2. The object is not marked for deletion ( or if the TX that requested the deletion has not completed )

### Indexes and snapshot isolation

- Store all objects in the index and filter out all objects which aren't visible to the current transaction
- loads of technical explanations that I don't actually understand (it goes into details with regards to what PostgreSQL does)

### Repeatable reads and naming confusion

- nobody knows what these mean
- Oracle calls snapshot isolation 'serializable'
- PostgreSQL calls is `repeatable read`

### Preventing lost updates

- read-modify-write cycles can cause these
- later write clobbers the earlier one
- It appears in situations such as
    1. incrementing a counter or updating an account balance
    2. making a local change to a complex value E.G. a json change
    3. two users editing the same wiki page

- Some solutions include

#### Atomic write operations

- ` UPDATE counters SET value = value + 1 WHERE key = 'foo';` this is typically enough
- another option is to force all atomic operations to execute only on one thread
- take an exclusive lock on the object when it's read and don't let any other trnasaction read it
- object relational mapping frameworks can cause you ending up writing code which performs unsafe read-modify-write cycles 

#### Explicit locking

- have the application explicitly lock the object
- This is done via the `FOR UPDATE` statement.