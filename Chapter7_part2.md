### Automatically detecting lost updates

- Atomic operations prevent lost updates by forcing read-update-write cycles to happen sequentially
- Can have r-u-w cycles run in parallel - if a lost update is detected by the `transaction manager`, abort the transaction and retry 
- DBs that don't implement lost update detection don't truly implement `snapshot isolation`
- Postgres, Oracle provide lost update detection / InnoDB and MYSql don't
- Lost update detection is great because if you forget a lock, you won't have issues

### Compare and set

- Databases that don't provide transactions will 
    1. Read the value before changing
    2. Compare the value it has read at 1. against the value when trying to update
    3. Update if the values match OR abort and retry if they don't ( Optimistic concurrency control)
- Databases might still allow you to read from the old snapshot, which means that you compare the old value against itself - ! no protection via compare and set !

### Conflict Resolution and Replication

- replication needs to be handled differently
- you cannot use compare and set or locks
- allow several concurrent writes to store conflicing values, then allow application code to deal with conflicts
- atomic operations are great for conflict resolution in replication, especially if they are commutative
- Riak 2.0 merges updates such that nothing is lost
- last write wins is the default in many replicated DBs

### Write skew and Phantoms

- dirty writes and lost updates are 2 kinds of race conditions
- must prevent via locks/atomic write ops or automatically by db
- refer to figure 7-8 on page 269 (digital) 247 (physical)
- DB implements snapshot isolation, so both doctors see that there are 2 doctors on call when they call in sick

### Characterizing Write Skew

- not a conflict in the sense that the same record got updated, but an integrity constraint got violated
- lost updates and dirty writes are a special case of write skew where we update the same object
- write skew occurs when 2 or more transactions read the same objects and only update some
- to prevent write skew, you need `true serializable` isolation
- atomic writes don't help
- most databases don't support constraints on multiple objects (but they support constraints on one)
- could do with triggers or materialized views
- can also lock all the rows involved in a transaction (query on page 248 phyiscal/ 270 digital )

### More write skew examples

- booking a meeting room
- multiplayer games with moving 2 different figures to the same spot
- claiming a username for a website (uniqueness constraints are enough to solve this)
- when shopping, 2 items can be inserted concurrently in the basket (this would lead to a negative balance)
- Pure Gym massage chairs :) 

### Phantoms causing write skew

- Pattern is the same
    1. Check precondition with select
    2. Go ahead or report error (based on precondition)
    3. If you go ahead, you write and commit the transaction

- The effect of the write changes the precondition of step 2.
- in the doctor's case, we check for the presence and update / in the other examples, we check for the absence and then add a row 
- If the query in 1. doesn't return any rows, you cannot lock anything!
- snapshot isolation avoids read phantoms, but doesn't avoid write phantoms
- A `phantom` is the effect of one transaction's write changing the search query for another


### Materializing conflicts

- For the meeting room booking case, you would need to artificially insert meetings in the table for the next 6 months increments of 15 minutes / when making a write, you lock a bunch of 15 minutes increments
- This is called `materializing conflicts` because the phantom is turned into a concrete row that can be locked
- it's hard to decide what needs to be materialized
- should be used as a last resort ( serializable isolation is preferred)

### Serializability

- isolation levels are hard to understand and they are implemented inconsistenly
- hard to tell if running at a certain isolation level is safe
- no good tools to detect race conditions/ you just get unlucky with the timing
- research suggests using `serializable isolation`
- 3 approaches to serializable isolation
    1. execute transactions in serial order
    2. two phase locking
    3. optimistic concurrency control

### Actual serial execution

- disallow concurrent transactions! run them only on one thread.
- this was rethought recently, and this happened because
    1. RAM is cheap and everything can fit into memory
    2. OLTP transactions are short and they make few reads and writes (OLAPs can be done from the same snapshot, they're mostly read only)

- Serial transactions implemented in VoltDB/ Redis
- throughput limited to only one cpu core
- transactions need to be structured differently to realize this

### Encapsulating transactions in stored procedures

- there are many steps involved in booking an airline ticket
- it would be great if we could commit everything in one transaction
- humans make up their minds slowly and we cannot have one long running tramnsaction
- Transactions are commited per HTTP request - this leads to interactive transactions
- single-threaded serial transaction processing disallows serial transactions - must use a stored procedure instead
- Refer to figure 7-9 on page 254 physical/ 277 digital

### Pros and cons of stored procedures

- each DB vendor has its own language (PL/SQL oracle, PL/pgSQL postgres)
- these languages are UGLY and lack the modern ecosystem
- DB code is hard to manage, tricky to test and debug, cannot collect metrics as easily
- badly written stored procedures can cause more issues than application code

- These can be overcome. 
    1. Modern implementations use existing general purpose programming languages / Redis uses Lua, Datomic uses Java, VoltDB uses Java
    2. Everything is kept in memory + stored procedures make transactions on single threads quite fast
    3. VoltDB executes the same stored procedure on each replica (must use deterministic API for current time and date stuff) - VoltDB requires stored procedures to be deterministic.

### Partitioning

