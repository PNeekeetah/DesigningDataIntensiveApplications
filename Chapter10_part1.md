Part III Derived Data

    - previous chapters assumed only one database in the application
    - application typically use a combination of several different datastores, indexes, caches, analytics systems, etc
    - the final chapters deal with integrating different data systems, some with distinct data models and access patterns into a coherent architecture

    Systems of Record and Derived Data

    - systems that store and process data can be grouped into two broad categories: systems of record and derived data systems
    - systems of record - the authoritative version of your data; new data is first written here with each fact represented (usually normalised) exactly once; any discrepancy with other system mean that this one is correct
    - derived data systems - data in such systems is the result of taking data from another system and processing/transforming it
    - derived data is redundant, in some sense, but useful in cases like read query performance
    - the distinction between the two systems is not always clear

10. Batch Processing

    - in online systems like the ones previously discussed, the response time should not be very long
    - three types of systems can be distinguished: services (online systems), batch processing systems (offline systems), stream processing (near-real-time systems)
    - services (online systems) - after receiving an instruction the service tries to handle it quickly, velocity being important
    - batch processing systems (offline systems) - jobs for processing large amounts of data and. after some time (minutes to days), produces some output data; the user is not usually waiting for the job to finish; usually run periodically and measured by throughput (the time it takes to crunch through an input dataset of a certain set)
    - stream processing systems (near-real-time systems) - middle of the two previous cases, it consumes inputs and produces outputs (rather than responding to requests) but on events (shortly) after happening instead of a set of input data
    - examples of batch processing include MapReduce, foundational to later solutions, and baring similarities to machines as old as ones used before the 20th century

    Section 1: Batch Processing with Unix Tools

    - an example of batch processing

    Simple Log Analysis

    - 6 steps have to be followed
    - albeit not always easy to read, it is powerful enough to process GB in seconds

    Chain of commands versus custom program

    - chains of Unix commands can be replaced by simple programs, if readability is important and the trade-offs are tolerable

    Sorting versus in-memory aggregation

    - some languages use hash tables of URLs to keep the number of times it is seen while Unix relies on sorting a list of URLs where multiple occurrences are repeated
    - choosing the best option depends on how many URLs one has - hash tables for smaller sets and sorting for bigger ones (where also efficient use of disks can be advantageous)

    The Unix Philosophy

    - the central idea behind Unix can be compared metaphorically to a plumbing garden hose
    - the four main ideas are: make each program do one thing well, expect the output of one to become input of another, design software to be tried early, use tools in preference to unskilled help
    - the sort tool is such an example

    A uniform interface

    - since the input of one must become output to another, the same data format, a compatible interface, must be used
    - in Unix this is a file descriptor, which is an ordered sequence of bytes, usually ASCII text
    - parsing is more vague, splitting a line being done in multiple ways

    Separation of logic and wiring

    - Unix also standardises standard input (stdin) and output (stdout), which has the advantage of programs that do no have to worry about particular file paths
    - some limits include difficulties with programs with multiple inputs and outputs

    Transparency and experimentation

    - the success of Unix is also based on the fact that it is easy to see what is happening (immutable inputs files to commands, possibility to end pipelines at any point, the output of one pipeline can be used as input in the next stage)
    - the biggest limitation of Unix tools is that they run only on a single machine (the likes of Hadoop offer solutions)

    Section 2: MapReduce and Distributed Filesystems

    - comparable to Unix tools but distributed across thousands of machines
    - a MapReduce job is alike a single Unix process: takes one or more inputs (which is not normally modified) and produces one or more outputs (which does not have any other side effect)
    - in MapReduce jobs read and write files on distributed filesystem named Hadoop Distributed File System (HDFS)
    - HDFS is based on the shared-nothing principle in contrast to Network Attached Storage (NAS) and Storage Area Network (SAN); shared-nothing approach requires no special or custom hardware, unlike shared-disk storage, only connection by conventional datacentre networks
    - HDFS consists of a daemon process running on each machine that allows other nodes to access files on that machine, the track of where file blocks are located being done using a central server names NameNode and therefore creating practically one big filesystem that can use the space on the disk of all machines
    - machine and disk failure are tolerated by replicating them on multiple location using various methods
    - HDFS is also highly scalable

    MapReduce Job Execution

    - MapReduce is a programming framework with which processing large datasets in a distributed filesystem like HDFS
    - going back to the log analysis earlier, MapReduce can reduce the steps into a single job
    - a job is created by implementing two callback functions: mapper and reducer
    - mapper - called once for every input record, extracts the key and value and generates any number of key-value pairs and doesn't keep states
    - reducer - collects all the values belonging to the same key in the key-value pairs and calls the reducer, which outputs records

    Distributed execution of MapReduce

    - the mapper and reducer only operate one record at a time, ignorant of the source of the inputs, the framework being the one that handles the complexities of moving data between machines
    - in Hadoop MapReduce, the mapper and reducer are each a Java class that implements a particular interface
    - the parallelisation is based on partitioning as discussed previously
    - for every input file, the MapReduce scheduler tries to run each mapper on one of the machines that stores a replica of the input file, if resources are sufficient (putting the computation near the data)
    - in most cases, MapReduce copies the data on the local machine the starts the map task passing one record at a time, the output being key-value pairs
    - the reduce task is also partitioned, determined by the number of input blocks, unlike the number of reduce tasks (configured by the author)
    - the generated key-value pairs are too large to be sorted with a conventional algorithm, this tasks being done in stages (each map task partitions by reducer, based on the hash of the key and then written to a sorted file on the mapper's disk)
    - after termination, the scheduler notifies the reducers that the output can be fetched from the mapper
    - the process of partitioning by reducer, sorting, copying data from mappers is known as the shuffle (albeit, no randomness is involved)
    - the reducer is called with a key and iterator that incrementally scans over all records with the same key, which might not fit in memory and the output is written to a file on the distributed filesystem

    MapReduce workflows

    - the number of problems that can be solved with a single MapReduce job is limited
    - jobs can be chained together in workflows, the output of one can become the input of another but must be configured manually
    - higher-level tools for Hadoop exist for setting up multiple MapReduce stages that are automatically wired together

    Reduce-Side Joins and Grouping

    - unlike databases, MapReduce has no concept of indexes in the familiar sense
    - when a job has a set of files as input, the entire content of all that files are read (full table scan)
    - despite being more "expensive" than index lookups, analytic queries calculates aggregates over a large number of records, also possible when the process happens in parallel across multiple machines

    Example: analysis of user activity events

    - in this example, it is best for the computation to be as much as possible local to one machine as random-access requests are too slow and if the database is remote, the batch job can become nondeterministic
    - a better approach is to take a copy of the user database and put in the same distributed filesystem as the log of user activity events

    Sort-merge joins

    - the framework partitions the mapper output by key and then sorts the key-value pairs, making the activity events and the user record IDs become adjacent to each other in the reducer input
    - the arrangement can be such that the reducer always sees the record from the user database first, followed by events in time-stamp order (secondary sort)
    - the reducer can perform the actual join logic easily
    - because the reducer processes all of the records for a particular ID, it only needs to keep one user record in memory at any one time (sort-merge join)

    Bringing related data together in the same place

    - a metaphor for this architecture is that mappers "send messages" to the reducers
    - when a mapper emits a key-value pair, the key acts like the destination address although it is only an arbitrary string
    - MapReduce separated the physical network communication aspect of the computation from the application logic

    GROUP BY

    - creating an equivalent of the function in database query languages can be done by setting up the mappers so that key-value pairs they produce the desired grouping (partitioning and sorting brings together all the records with the same key in the reducer)
    - sessionisation - collating all the activity events for a particular user session in order to find out the sequence of actions the user took
    - sessionisation can be implemented session cookies, user IDs, other identifiers

    Handling skew

    - “bringing all records with the same key to the same place” is no longer possible if a very large amount of data relates to a single key
    - such asymmetries are known as linchpin objects or hot keys
    - collecting all activity related to a "celebrity" can lead to a skew (also called hot spots), a reducer that must process significantly more records than the others, potentially making the system dependent on this slowest reducer
    - an algorithm that can compensate for this problem is the skewed join method in Pig, which runs a sampling job to determine the keys that are hot; during the actual join, mappers send any records related to a hot key to one of several reducers, chosen at random
    - other techniques such as sharded join from Crunch is similar but requires hot keys to be specified explicitly
    - in Hive, skewed join hot keys must be specified explicitly in the table metadata and stores records related to those keys in separate files from the rest
    - grouping records by hot keys and aggregating them can be performed in two stages: first, records are sent to a random reducer and second, the values from all the first-stage reducers are combined into a single value per key




