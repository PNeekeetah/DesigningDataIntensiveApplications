375 - 321 = 54 / 2 = 27

Start: 321 
End : 348

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

-  storing all the data on only one replica would provide linearizability however it does not provide fault tolerance 

-  single leader replication is potentially linearizable however it might not be because it uses snapshot isolation or because of concurrency bugs 
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
