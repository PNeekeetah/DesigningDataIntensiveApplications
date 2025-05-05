## Beyond Map Reduce

- many other tools like MapReduce are available, despite the hupe
- it's a good learning tool
- implementing a MapReduce job is fairly difficult - you need to write your own joins
- Pig, Hive, Cascading, Crunch are all abstractions built on top of MapReduce
- MapReduce is great for proceessing arbitrary amounts of data with unpredictable termination rates on a cluster of machines - other frameworks might process your data more quickly though

## Materialization of Intermediate State

- MapReduce jobs are independent from one another
- only points of contact of a MapReduce job are its input and output
- Job A needs to be configured to output to the same directory as job B is reading from - and then job B needs to wait for job A if you were to pipeline multiple MapReduce jobs
- This is great for loose coupling of jobs ! (e.g. output of one team is consumed by several other teams)
- Often, the output of one job is actually used by the same team / this is an `Intermediate Step` / for 50-100 MapReduce job workflows, there can be many intermediate steps
- The process of writing the intermediate step is called `Materialization` ( compute the result and store it somewhere rather than presenting it on-demand) 
- in contrast, unix pipes don't materialize the intermediate steps / they stream the output to the input instead
- There are downsides to materializing the state
    1. A job can start only when all preceeding jobs have finished 
    2. Mappers are redundant because they just read the output from previous reducers/ you could chain reducers together (technically)
    3. Storing intermediate steps in a distributed filesystem means that data is stored across several machines

## Dataflow engines

- Flink, Spark and Tez appaeared ti try to minimize MapReduce's downsides
- They handle an entire workflow as one job ( rather than having multiple subjobs)
- These systems are called `Dataflow engines`
- One record at a time is processed on a single thread by a user defined function - inputs are partitioned to parallelize work - outputs are copied over the network
- These functions don't need to alternate map and reduce stages - several options exist when connecting outputs to inputs :
    1. Repartition and sort - similar to MapReduce
    2. Keep partitioning but drop the sorting ( e.g. because building the hash table jumbles up the order)
    3. Output of one operator can be sent to all partitions of the join operator for broadcast hash joins

- There are advantages to doing the above:
    1. sorting can be done ONLY when it's actually needed
    2. No unnecessary map tasks - the mapper is incorporated into the preceding reduce operator
    3. You declare all data dependencies in a workflow - the scheduler knows where data is produced and consumed, so it can delegate tasks to the same machine where it is heavily produced/ consumed - this can eliminate network overhead
    4. The intermediate step is kept in memory or written to HD rather than writing it to the distributed file system - quicker!
    5. operators execute when data is available - they don't wait for preceeding jobs to be ready
    6. You reuse existing JVM processes rather than spinning up new tasks ( you avoid cold starts )

- You can use dataflow engines to do the same computations as a MapReduce workflow significantly faster !
- Pig/ Hive/ Cascading can use either Spark or MapReduce by specifying a config
- Tez is a thin library/  Spark and Flink are big frameworks

## Fault Tolerance

- Materializing the intermediate state to the HDD offers durability - just restart the task in map reduce !
- Tez/ Spark / Flink don't store an intermediate state / if a job fails, they either recompute from data that is still available (a prior intermediary stage ) or they recompute from the original data
- these frameworks keep track of how data was computed
- Spark uses the resilient distributed dataset abstraction for tracking data ancestry
- Flink checkpoints operator state ( can resume from  that state)
- When recomputing data, is the computation deterministic ? If yes, attempt from the last known checkpoint, otherwise kill all downstream operators
- Using clocks, reading hash sets and using statistical algorithms all represent sources of non-determinism - you have to avoid these to build reliable worflows
- If intermediary state is small enough, you're better off storing it than recomputing it

## Discussion of materialization


- MapReduce is like writing intermediary outputs to files, Flink is more like piping data into a Unix system
- sorting needs all the data in order to work correctly / other parts of the workflow can be executed in a pipeline manner though
- The output is still written to the HDFS in the end /you just save yourself writing intermediate states

## Graphs and iterative procesing

- PageRank is one of the most popular graph analysis algorithms ( how popular is a page given the references it has )
- Dataflow engines arrange operators like a DAG - not the same as graph processing ! The data flows through a graph-like structure in dataflow engines, whereas graph processing is processing objects which are graphs !
- Map reduce cannot implement the idea of `repeating until done` since it performs a single pass on the data / this is implemented in iterative style
    1. A scheduler runs a batch process to calculate one step
    2. It checks whether it was the last step (e.g. there's no data left to process)
    3. It reruns step 1 if not

- MapReduce is inefficient for this


## The Pregel processing model

- The Bulk Synchronous parallel model of computation has become popular - popularized by Google's Pregel paper
- optimization for batch processing graphs

## Fault Tolerance

- the state of all graph vertices is checkpointed to durable storage at the end of an iteration
- nondeterministic computations are rolled back / deterministic ones are recovered from the previous state

## Parallel execution

- if the graph can fit in memory ( be it RAM or HDD/SSD ), it will be fastest to compute it on a single machine, even if running on a single thread
- If the data cannot fit in durable storage, you have to use something like Pregel
- Parallelizing graph algorithms is ongoing research

## High-Level APIs and Languages

- MapReduce can process petabytes of data on 10_000 big machine clusters
- Focus is now on improving the programming model, improving efficiency of processing and broadening the set of problems that can be solved by map-reduce
- Writing MapReduce jobs by hand is laborious, hence the popularity of higher level languages and APIs
- High level interfaces require less code
- You can develop interactively by writing analysis code in the shell and iterating over that

## The move toward declarative query languages

- you can allow the framework to analyze the properties on the join inputs and allow it to select the join algorithm fit for the task
- Spark, Flink and Hive have cost-based optimizers
- Better than specifying in imperative style HOW to do it 
- you don't need to remember which joins are available ! (and which join is used could impact processing speed)
- The freedom to run arbitrary code is what distinguishes batch processing programs from massively-parallel processing databases - DBs have the option to write user specified code, but sharing it is cumbersome
- Batch processing engines can match MPPs due to declarative queries but have added flexibility

## Specialization for different domains

- Standard processing patterns keep reoccuring, it's useful not having to re-implement them
- Reusable implementations are emerging - Mahout implements ML algorithms on top of MapReduce, Spark and Flink
- MADlib implements similar functionality inside a relational MPP
- K-nearest-neighbours is useful for spatial algorithms
- In the end, Batch processing algorithms and MPPs end up looking very similar 

