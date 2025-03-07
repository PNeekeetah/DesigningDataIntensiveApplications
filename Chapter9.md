# Consistency and Consensus 

- the best way to handle an error is to let the entire service fail 
- the second best way of handling a failure is to keep the service functioning incorrectly despite the fact that a fault has occurred 
- consensus is the ability of all the nodes to agree on something 
- getting all the nodes to agree on something is a difficult problem 
- once you have an implementation for consensus you can use use it for various purposes 
- you get database nodes to reach consensus and elect a new leader to avoid the split brain problem 
- consensus has been studied for a long time and whatever is presented in this chapter offers only an intuitive overview

## Consistency Guarantees

- if you look at a 2 replicas of a database at the same time, you will likely see different data on both of them 
- this is likely to happen regardless of the replication method which was used 
- most databases provide eventual consistency which means that at some point the data on all the nodes will be the same 
- consistency would be better named `convergence` 
- eventual consistency is a very weak guarantee because it doesn't tell you WHEN you will be able to read that data 
- eventual consistency is very different from variables in a single threaded program 
- databases which provide eventual consistency might look fine until it gets pushed to its limits or a fault appears in the system or you get high concurrency 
- stronger consistency models come off and at a performance cost 
- stronger consistency models are easier to reason about when developing
- there are some similarities between the level of isolations that exist for transactions and consistency 
- distributed consistency is about coordinating replicas when faced with delays and faults 

### Linearizability 
 
-  make the system look like there is only one replica/one copy of the data and make it look as if all operations are atomic 
-  maintaining the illusion of a single replica means being able to guarantee that the value that was just read is the most up-to-date version of the value and it is not read from a stale cache or from a replica that was not yet updated 
-  refer to figure 9-1 on page 324 physical copy or 346 pdf version 

### What Makes a System Linearizable?

We get an overview of what linearizability means by going through a few worked examples:
    refer to figure 9 - 2 on page 325 physical copy and page 347 on the PDF version 
    refer to figure 9 - 3 on page 327 physical copy and page 349 on the PDF version  
    refer to figure 9 - 4 on page 328 physical copy and page 350 on the PDF version 

-  there might exist multiple writes in a system at any given point and multiple concurrent reads might be happening at the same time 
- when these reads are executed there must be a point in time when the `old` value stops being read and the `new` one starts being read instead rather than having an alternation between the old value and the new value 
- the formal definition of linearizability is that it is possible to test (and computationally expensive) whether the behaviour of a system is linearizable by recording the timings of all the requests and all of the responses and checking whether these can be arranged in a valid sequential order 

!!! linearizability is different from serializability 
- serializability means that transactions behave as if they have been executed in a certain order 
- linearizability on the other hand is a recency guarantee on reason rights of register 

- databases may provide both serializability and linearizability 
- this is called strict serializability 
- two phase locking and actual serial execution are typically linearizable 
- serializable snapshot isolation is not linearizable by design 

### Locking and leader election 

-  systems which use single leader replication must ensure that there is only one leader active at a time 
-  this is typically enforced by having the leader acquire a lock 
-  it doesn't matter how the lock is implemented, but it must be linearized 
-  all nodes must be able to agree on which node owns the lock
-  services such as `Zookeeper` and `etcd` are often used to implement distributed locks and leader election 
-  Apache Curator provides higher level recipes on top of Zookeeper to achieve linearizability 
-  a linearize storage service is the foundation for these coordination tasks 

### Constraints and uniqueness guarantees 

-  a username or email must uniquely identify a user 
-  to enforce such a constraint for your system you need linearizability 
-  the situation is similar to a lock 
-  similar issues arise if you want to ensure that your bank account never goes negative 
    that you don't oversell items 
    that you don't overbook your flights 
-  you could treat the constraints of such a system more loosely for example by allowing over booking and then compensating your passengers 
-  `uniqueness` constraints such as the ones you find in a relational database require linearizability 
-  other types of constraints such as `foreign keys` can be implemented without requiring linearizability 

### Cross channel timing dependencies 

-  in figure 9 - 1 Bob would not have checked the score if Alice did not explain that Germany has won 
-  the linearizability violation was noticed only because there was an additional channel 
-  refer to figure 9 - 5 on page 232 physical copy and page 354 on the PDF version 
-  the problem arises because there are two communication channels  
-  if you have control over the additional channel you can use similar approaches to that of `reading your own writes` at the cost of additional complexity 

### Implementing linearizable systems 

-  storing all the data on only one replica would provide linearizability - it does not provide fault tolerance though
-  single leader replication is potentially linearizable however it might not be if it uses snapshot isolation or if concurrency bugs occur 
-  you also run the risk of having a split brain situation and then losing some of the committed writes in case of a failover 
-  this violates durability and the linearizability 

-  consensus algorithms are linearized and they bear resemblance to single leader replication 
-  consensus protocols contain measures to prevent split brain 
-  this is how zookeeper works 

-  multileader replication is not linearizable because multiple writes happen concurrently and then they get asynchronously replicated to other nodes 
-  this this can produce conflicting writes in the database 

-  leaderless replication is probably not linearizable 
-  you can potentially get strong consistency by requiring read and write quorums
-  `last write wins` conflict resolution methods based on the time of the day are almost certainly nonlinearizable because clock time stamps cannot be guaranteed to be consistent 

### Linearizability and quorums 

- refer to figure 9 - 6 on page 334 physical copy and page 356 PDF version 
- in this example it is shown that even though we've reached quorum we still have a race condition -> non-linearizable
- this happens because of the network delay when writing to replicas one and two 
- Dynamo style quorums can be made linearizable at the cost of performance
- Cassandra provides read repair in the presence of non-concurrent writes
- Riak does not
- Only linearizable reads and writes can be implemented like this - compare and set cannot be
- Dynamo style quorums are most likely not linearizable 

### The cost of linearizability 

-  refer to figure 9 - 7 on page 335 on the physical copy or 357 on the PDF version  
- in a single-leader multi datacenter scenario, the system becomes non-linearizable in the presence of a network interrupt. replicas outisde  of the leader's datacenter cannot provide the most up to date value
-  this makes the application unavailable for the client's connected to the data centre without the leader 

### The CAP theorem 
- if the application requires linearizability and some replicas are disconnected it effectively means that the disconnected replica has become unavailable 
- if the application does not require linearizability it can be written such that replicas process requests independently but the reads and writes will not be linearized 
- CAP is a sliding scale between consistent but unavailable and available but inconsistent 
- CAP is best thought of as `either consistent or available when partitioned` 
- CAP cannot describe systems well because it's very unidimensional - it considers only partitioned networks and the linearizability consistency model ( more types of faults and consistencies in practice ) 
- CAP has little practical value when designing systems 

### Linearizability and network delays 

-  RAM on a multi-core CPU is not linearized 
-  this happens because of the CPU cache and because we typically try fetching values from the cache rather than fetching it from the RAM  
-  linearizability is lost 
-  in this case linearizability is dropped for performance reasons not for fault tolerance 
-  linearizability is slow 
-  performant systems conflict with linearizability

### Ordering guarantees 

-  Ordering is important in single leader systems because replicas copy the leader's write ahead log ( consider what happens when transactions get applied in a different order )
-  we have seen that conflicts can arise in multileader systems due to concurrent reads and writes 
-  serializability is about ensuring that transactions behave as if they have been executed one after another 
-  we use timestamps and clocks in an attempt to create order 
-  there exists a deep connection between ordering, linearizability and consensus 

### ordering and causality 

-  ordering helps preserve causality 
-  we have seen that it is confusing to see the answer of to a question before the question was asked - questions and answers must be causal
-  in the case of several leaders it mean that a replica might see a row being updated before it is created
-  causality implies that the row must be created BEFORE being updated 
-  in concurrent writes
    1. A happened before B
    2. B happened before A
    3. They happened concurrently
- consider the application with on call doctors where two doctors tried to take themselves off the on-call at the same time 
-  consider the example where a  person finds the score of a match from a different channel but the website provides different information 
-  causality imposes an ordering on events | CAUSE comes before EFFECT

- a system which obeys the order imposed by causality is said to be `causally consistent` 

### The causal order is not a total order 

-  causal ordering allows you to compare any two numbers 
-  mathematical sets are not totally ordered 
-  linearizability means a total order 
-  causality on the other hand does not impose a total order  - it imposes a partial order 
- some operations are ordered with respect to each other but you cannot compare their orders to others 

### Linearizability is stronger than causal consistency 
-  the relationship between linearizability and causality is that linearizability implies causality 
-  linearizability makes systems easier to reason but imposes severe performance restrictions

- causal consistency allows a system to remain available in spite of network faults - it's a good middleground
- many systems which appear to require linearizability in fact require causal consistency 
- not a lot of these have made it onto production systems YET 

### Capturing causal dependencies 
-  in order to maintain causality on replicas you need a partial ordering on the events that happened and when you replay them you need to ensure that you maintain the causal dependency between the events 
- you cannot register events on a replica before they happened (A -> B -> C / you cannot register C first)
- the reference to the CEO investigation because he's a criminal is funny 
- version vectors can be generalised to this 

### Sequence number ordering 

- can be cumbersome to keep track of all causal dependencies
- can keep causal ordering via number sequences

## Noncausal sequence number generators

- sequence numbers are hard to generate in non single leader configurations  
- solutions include:  
  - each node generates numbers only from a certain pool (e.g. %2, %n)  
  - attach a Time of Day timestamp to each number  
  - pre-assign blocks of numbers that each node can generate  

- All of these are not consistent with causality  
  - counter for %2 == 0 may generate more numbers than counter for %2 == 1  
  - timestamps are subject to clock skew  
  - nothing stops a node from pre-assigning 1001 to 2000, then 0 to 1000  

## Lamport timestamps  

- most cited distributed systems paper  
- you can generate sequences of numbers consistent with causality  
- generate a tuple of the form (<MAX_COUNTER_SEEN>, <NODE_ID>)  
- refer to figure 9-8 on page 346 (368 on the PDF version)  
- total ordering happens by comparing the counter first, then the node ID  
  - a slower process may jump from 1 to 6 on its counter if a faster node has reached the value 6  
  - version vectors distinguish whether 2 operations are concurrent <=> Lamport timestamps enforce a total ordering  

## Timestamp ordering is not sufficient  

- consider the case for the system which needs to assign unique emails  
- this approach works well when looking in retrospect - it doesn’t work when trying to decide on the spot which user wins the username assignment  
- if the username assignment problem, you need to check with all the nodes to know when the order is finalized  
- to implement a uniqueness constraint for a username, it's not sufficient to have total ordering / you need to know when the order is finalized  
  - you need to establish that nobody else can claim this username before you insert it into your db  

## Total order broadcast  

- if the program runs on a single CPU, you can easily define a total ordering of operations - it's the order in which the ops were executed  
- single leader replication is more powerful than timestamps alone because timestamps may be skewed  
- how do you scale a system which has a throughput greater than what a single leader can handle?  
- how do you handle failover if the leader fails?  
- the name of this problem is *Total order broadcast* / *atomic broadcast*  

- partitioned DBs with a single leader per partition maintain ordering in the partition, but they cannot offer consistency guarantees across partitions  
- the Total Order Broadcast is described as a protocol to exchange messages between multiple nodes  
- It must satisfy:  
    1. Reliable delivery - messages aren’t lost  
    2. Totally ordered delivery - messages are delivered in the same order  

- A correct algorithm for TOB must ensure both 1 and 2 even if a node / the network is faulty  
- messages cannot be delivered when the network is down, but the algorithm can retry when the network is restored (and then deliver the messages in order)  
