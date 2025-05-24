## Aiming for correctness

- Stateless services are not fussy when it comes to fixes
- stateful services (e.g. connected to a DB) are and the mistake might last forever
- Atomicity, Isolation and durability have been building blocks for 4 decades, but sometimes their guarantees are weak
- transactions can be abandoned for better performance and for messier semantics
- consistency is an afterthough
- cannot detemrine whether it's safe to run an app at a certain isolation level
- simple solutions can appear correct when concurrency is low - blows up later !
- safety guarantees of products is different from their behaviour - even if there weren't such problems, you still have to configure it correctly ! (1 more avenue of messing up) ( especially hard if we're talking quorums or weak isolation levels)
- if the app can tolerate corruption or dataloss, just let it happen 
- transactions aren't going away, but there's a limit to the scale and fault tolerance you can achieve


## The End to End argument for databases

- Just because your database has some strong safety properties (serializable transactions ), it doesn't mean the app is free of corruption
- if the app writes incorrect data or deletes it, tough luck!
- take into account that people fail and applications fail
- append only data is better because it's easier to ignore bad data than it is to recover destroyed good data

## Exactly once execution of an operation

- if you were to process a message exactly once, it means that you'd need to drop the data once an error occurs
- trying again carries the risk that it was successful the first time around
- processing twice is a form of data corruption 
- exactly once means arranging the computation such that the final effect is the same regardless of whether processing failed several times or it was succesful the first time around
- best way is to make operations idempotent (and keep track of operation IDs and ensure fencing when failing over)

## Duplicate suppression

- having to drop dupes is something which TCP does as well ( packets are numbered for reordering and dropping duplicates)
- looking at figure 12-1 from page 517 ( page 539 digital version), commits don't work like that
- 2PC protocols break the 1 to 1 mapping between transactions and TCP connections to allow a coordinator to reconnect to the database after a failure - this doesn't ensure that the transaction's executed only once
- usual deduplication mechanisms don't help (e.g. when double submitting post requests / double get / update requests aren't a problem)

## Operation identifiers

- you have to consider the end to end flow of the request
- you could include an ID or hash the form's fields to get a UUID - when it arrives at the database, you only process it if the UUID isn't in the Database already - see Example 12-2 on page 518 ( 540 in the digital version)
- application level check and insert might fail under nonserializable isolation levels
- updates to account balances don;t have to happen in the same transaction since they can be derived from the requests table

## The end-to-end argument 

- TCP, database transactions and stream processors cannot rule out dupes by themselves
- solving the problem requires an end to end solution - a transaction identifier whihc is passed from end user client to database
- checksums built into ethernet, TCP and TLS can detect corruption of packets in the network,  but they cannot detect corruption due to bugs in the software at the sending or receiving end or disk corruptuon
- password from your home WiFi protects against people snooping WiFi traffic, but not against people on the internet
- TLS/SSL protects against network attackers, but not against server compromises
- Only end to end auth and encyrption protects against these
- low level features don't provide these end to end protections by themselves, but they reduce the probability of issues happening at higher levels so they're still useful

## Applying end to end thinking in data systems

- just because an app uses some strong low level safety properties, it doesn't mean that it's guaranteed to be safe from data loss
- fault tolerance mechanisms are hard to get right, but they server their purpose well - we don't live in a world where we can wrap up the remaining high level fault tolerance machinery in one abstraction

- transactions are expensive , heteorogeneous storage technologies make everything harder AND it results in people trying to reimplement safety guarantees in application code where they often mess up

## Enforcing constraints

- we have the example of the request ID which offers end to end duplicate protection
- we have thought previously about enforcing uniqueness constraints (plane seats, file names etc)
- we also have account constraints (don't go below 0), don't sell more items that you have, don't overbook meeting rooms - but uniqueness constraints require consensus

## Uniqueness constraints that require consensus

- In distributed settings, enforcing a uniqueness constraint requires consensus
- consensus is achieved by making a single node the leader / if you don't want to funnel all data through a single node, you're stuck having to solve consensus again
- uniqueneess checking can be scaled out by partitioning based on the value that needs to be unique - if you need uniqueness by request ID, ensure all requestss are routed to the same partition / if you want usernames to be unique, you can partition by hash of username

- Async multi master replication is ruled out because multiple masters can accept conflicting writes
- you need sync writes to reject conflicts immediately

## Uniqueness in log based messaging

- the log ensures that consumers see messages in the same order
- this is total order broadcast 
- in the unbundled DB approach, we can use similar approaches to uniqueness constraints
- Stream processors consume data in a log partition sequentially, so it can decide which of the operations came first
- for usernames, accept the ones that don't exist in a DB and reject the others
- clients wait for the output messages to be rejected or not
- you can scale this approach by adding more partitions
-  works not only for uniqueness constraitns, but for others as well

##  Multi partition request processing

- atomic operations which satisfy constraints are harder to execute when partitions are involved
- for example 12-2, there could be 3 partitions 
- in a traditional DB, you'd require an atomic commit across all 3 partitions
- it can also be done without an atomic commit 
    1. give the transfer request an ID and append it to a log
    2. stream processor reads the log of requests and it emits a debit instruction for A and a credit instruction to account B
    3. processors get rid of dupes and apply changes

- you can also ensure that the account in not overdrawn by having a third stream processor that maintaisn account balances and validates transactions
- (I will not go in all the details here)

## Timelines and integrity

- Transactionsare tpically linearizable ( readers only read it after writers have finished writing it)
- not the case when unbundling an operation across multiple stages of stream processing
- consistency conflates to two different requirements 
    1. Timelines
    -   users observe the system in an up to date state
    - if a user reads from a stale copy, they may observe it in an inconsistent state
    - inconsistency is temporary, it's resolved by trying again
    - CAP theorem uses consistency in the sense of linearizability (strong timeline guarantee), but read after write can also be useful
    2. Integrity
    - corruption of absence
    - Derivation from a base dataset must be correct
    - DB indexes must reflect the contents of the DB, otherwise it's useless
    - if you violate integrity, you have permanent inconsistency
    - atomicity and durability are important for preserving integrity
    
- Timeline violations ere eventual consistency, integrity violations are perpetual inconsistency
- Integrity >> timelines
- Credit cards have a lag and that's fine, but it would be CATASTROPHIC if the merchant didn't receive their money

## Correctness of Dataflow systems

- ACID transactions provide both timeline and integrity guarantees
- for event based dataflows, timelines and integrity are decopled 
- integrity is central to streaming systems

- exactly once or effectively once is a mechanism for preserving integrity - losing or processing twice are integrity violations 
- reliable stream processing can preserve integrity without requiring distributed transactions or an atomic commit protocol with better performance
- We can achieve integrity through:
    1. COntent of write ops is a single message
    2. Derive state updates from a single message using deterministic derivation functions
    3. Pass a client generated req-ID at all processing levels
    4. Making messages immutable and allowing derived data to be reprocessed

# Loosely interpreted constraints

- we cannot avoid funelling everything through a single node even for stream processors
- many applications can get away with weaker uniqueness notions

- you can send a compensating transaction ( apologize if a username tries to take the same name)
- if they order more items than you have in the warehouse, order more and apologize for the delay ( offer a discount )
- hotels and airplanes overbook and provide a complementary room + refunds
- persons can overdraft, but you limit how many people can overdraft - minimize risk to banks!

- Perfectly acceptable to violate and constraint and fix it up later
- the apology (e.g. money ) is low enough in most cases to justify - suck it up!
- If apologies are acceptable, checking all constraints before writing your data is not needed! better write optimistic code :)
- apps still require integrity ! don't lose reservations or have money disappear

## Coordination-avoiding data systems

- dataflow system can maintain integrity guarantees on derived data without atomic commits, linearizability and sync cross partitions coordination
- strict uniqueness constraints require timelines and coordination, but many apps are fine with loose constraints that are fixed later

- data management services can be provided for many applications without requiring coordination while still giving strong guarantees
- a system could operate aacross serval datacentres in a multi leader configuration and any 1 datacenter can continue independently of others
- such a system has weak timeline guarantess , but it can have strong integrity guarantees
- XA transactions are not required
- no need to coordinate everything if only a small part of the application needs it
- timelines potentially reduce your apologies and inconsistencies, but it also reduces your performance - you can't reduce apologies to 0, but you can find a tradeoff - you can find a sweet spot without too many inconsistencies and too many availability problems

## Trust, but Verify

- we call these assumptions our `system model` 
- we assume that processes cna crash, machines can lose power, multiplication always returns the correct result
- these assumptions are reasonable, but it's hard to get anything done if we worry about computers messing up all the time
- do violations of our assumptions happen often in practice ?

- data can pe corrupted on harddisks and data can be corrupted over TCP

- some application he worked on in the past had reports that could only be explained by random bit flips

- for enough devices running your software, EVERYTHING becomes possible

## Maintaining integrity in the face of software bugs

- MySQL has failed to maintain a uniqueness constraint
- PostgresQL shoudl be robust enough and both MySQL and Postgres are well regarded - less mature software has it worse
- application code has way more bugs since application don't receive nearly the same amount of review and testing as DBs do
- Consistency in the ACID sense is based on the idea that DBs start off in a consistent state and dbs transform data from one consistent state to another
- It makes sense only if you assume your transaction is free of bugs! ( or if the app uses the DB correctly ) - DB integrity cannot be guaranteed otherwise

## Don't just blindly trust what they promise

- software and hardware is corrupted soooner or later
- checking data integrity is known as auditing
- auditing is not only for financial apps (but it's valuable especially there because people know mistakes happen)
- large scale systems such as HDFS and Amazon S3 continuously read back to disk files to ensure that bits aren't corrupted (to mitigate silent corruption)

- schoedinger's data - you can't be sure it's there until you read it! Don't trust that it's still there

## A culture of verification

- HDFS and S3 still have to assume that disks work correctly most of the time, but still audit themselves
- many systems don't do this
- ACID databases have led to a cultuure of developing apps on a basis of blindly trusting technology - auditing mechanisms are not deemed not worth it
- The DB landscape changed, weaker consistency became the norm under NOSql and less mature storage tech is now widely used - audit mechanisms are not developed as much yet though

## Designing for auditability

- If a transaction mutates several objects in the DB, it's difficult to tell after the fact what the transaction meant
- the invocation and application of the logic is transient and can't be reproduced

- event based systems provide better auditability 
- user input is represented as an event and derivation can be made deterministic and repeatable - rerunning the logs will produce the same updates

- being explicit about dataflow makes WHERE your data came from much clearer 
- integrity checking is more feasible
- use hashes to check that the event storage has not been corrupted
- a deterministic dataflow makes debugging your system easier - Time travel debugging!

## End to end argument again


- if we can trust that every part of the datasystem is doing it's job, check periodically that the integrity of your data
- corruption can propagate downstream otherwise and it's gonna be much harder and expensive to track it down

- having continuous end to end integrity checks gives you increased confidence for your system

- you can meet changing requirements better 

## Tools for auditable data systems

- Not many datasystems make auditability their main concern
- some applications log all changes to an audit table, but guaranteeing the integrity of the log and the database is still difficult
- transaction logs can be made tamper proof by periodically signing it, but it doesn't guarantee that the correct transactions went into it
- proposal to use crypto to prove the integrity of your systems

- from a data systems POV, they contain interesting ideas
- they are distributed databases with a data model and a transaction mechanism
- replicas continually check each others integrity and use consensus to agree on the transactions that were executed

- Byzantine fault tolerance aspect of these technologies is dubious
- proof of work is wasteful
- integrity checking aspects are interesting

- crypto auditing and integrity often relies on merkle tress - trees of hashes that can be used to efficiently prove that a record appears in a dataset

- integrity checking can be used more widely in datasystems
- work is needed to make them just as scalable without crypto auditing