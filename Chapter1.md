# Reliable, Scalable, Maintainable applications

1. Foundational Concepts

    Section 1: Thinking about data systems

    -- Applications today are data-intensive, not computationally intensive.
    
    -- Most data-intensive applications nowadays need to:
    1. Store data in a database.
    2. Cache results of expensive operations.
    3. Search data by keywords via a search index.
    4. Send messages to other processes asynchronously using stream processing.
    5. Periodically crunch large amounts of data using batch processing.

    -- Systems have 3 qualitites
    1. Reliability - how resistant is it in the face of adversity?
    2. Scalability - how much load can the system handle ?
    3. Maintainability - how easy is it to make changes to the system ?


2. Reliability

    Section 2: Reliability

    -- The system's ability to work correctly despite one or multiple faults
    -- A fault is a component deviating from its spec
    -- Prevent faults from turning into system wide failures
    -- Systems can be mode more reliable by artificially introducing faults (Netflix's Chaos Monkey)

    Section 3: Hardware faults

    -- Any physical phenomenon which prevents the system from running (blackouts, hard disk failures)
    -- Adding redundancy typically solves this
    -- Moving towards software fault tolerance in addition to/ instead of hardware fault tolerance

    Section 4: Software errors

    -- Unlikely for multiple hardware faults to occur at the same time, but likely for software faults
    -- Hardware faults are uncorellated typically, software faults are correlated
    -- Hard to prevent

    Section 5: Human errors

    -- Leading cause of errors ( hardware faults accounted only for 10 - 25% of the issues )
    
    -- Prevention includes
    1. Designing systems to minimize errors - encourage the right and discourage the wrong
    2. Decouple places where most issues occur
    3. Testing , from unit to E2E
    4. Allow easy recovery from human error
    5. Setup monitoring
    6. Good management practices

    Section 6: How important is reliability?

    -- Not having reliability for nuclear stations potentially means danger, unreliability for ecommerce platforms means customer disatissfaction and loss of revenue
    -- Can sacrifice reliability sometimes to keep deveolpemnt costs low.

3. Scalability and Performance

    Section 7: Scalability

    -- Cannot really say that a system doesn't scale - the questions are "What can we do if we see this kind of growth in our system"
    -- Scalability issues can come from higher user base or from higher volumes of data

    Section 8: Describing load
    
    -- Must be able to describe current load in our system
    -- Potential examples for load description are:
    1. Read to write ratio in database
    2. Requests per second
    3. Simultaneous active users
    4. Cache hit rate
    
    -- Twitter's maiun operations are: Tweet posting (4.6 k average) and Home Timeline update 
    -- To handle the home timeline update, there are possibly 2 approaches: 
    1. Do a join on several tables to get the updates ( pull )
    2. Insert into the home timelines the results ( push )
    -- 1. was slow, 2 was okay for a while, now using a mixture of both of them. Use 2 for most cases, use 1 for celebrities.

    Section 9: Describing performance

    -- When load increases, if the components stay the same, how does performance degrade? 
    -- How much do you need to increase the performance of your components if you want the same performance
    -- Batch processing systems care about throughput (e.g. Hadoop)
    -- Online systems care about response time ( from request to response )
    2 similar metrics 
    -- Latency - how long a request awaits to be serviced
    -- Response - how long does the user wait to get a response
    -- The mean is typically useless for response times. You want to know the median, called the 50th percentile. 
    -- There are other interesting percentiles such as the 99th percentile or the 99.9th percentile.
    -- Amazon noticed that 100ms delay in response time drops down sales by 1%
    -- Percentiles are used to describe SLOs (service level objectives) and SLAs (service level agreements). These set the terms for customers to demand a refund if the requirements are not delivered.


    Section 10: Percentiles in practice

    -- Should keep a rolling average of the past 10 minutes 
    -- Sorting response times might be impractical / forward decay, t-digest are good alternatives or approximating the percentiles
    -- Aggregate data in histograms, don't average percentiles from different machines 


    Section 11: Approaches for coping with load

    -- Slowest request of the whole bunch in the backend dictates how slow the system is
    -- Architecture which copes with a certain type of load is likely unsuitable for 10x the load
    -- `Horizontal scaling` or `vertical scaling` (shared nothing - requests get distributed to multiple machines)
    -- Some systems are `elastic` - they automatically scale with the load
    -- Manually scaled systems are easier to implement
    -- Easy to distribute `stateless` services across several machines, hard to distribute `stateful` systems across machines
    -- Must consider the access patterns when scaling

4. Maintainability

    Section 12: Maintainability
    
    -- Lots of pain points with maintaining legacy software
    -- Systems should be designed to be operable, simple and evolvable

    Section 13: Operability. Making life easy for operations
    
    -- Some of the things operability includes are:
    1. Monitoring the health of the system
    2. Tracking down problems
    3. Patching software
    4. Future planning ( anticipating future problems and solving them )
    5. Maintaining the system's security
    6. Preserving information about the system even though people come and go

    Section 14: Simplicity. Managing complexity

    -- Complexity is accidental if it doesn't stem from the problem we're trying to solve.
    
    Section 15: Evolvability. Making changes easy

    -- Refactoring and Test Driven Deveolpemnt are Agile tools that are used in systems where change occurs often
    -- Simple and easy to understand systems are easier to work on that complex ones
    -- Agile works with the small scale, DDIA works with answering larger scale problems E.G. how to go from Twitter's first home timeline update mechanism to the second one 