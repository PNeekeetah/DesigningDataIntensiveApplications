# Storage and Retrieval

## The data structures that power your database

- Log structures and b trees are the main ones
- you can design a "viable" database by appending logs to a file and then grepping for the key
- appending to a file is actually fast - retrieval is linear and it will cause problems
- you can speed up database reads, but that comes at a cost with how fast you can write (e.g. via indexes)

## Hash indexes

- like most dictionaries
- the key specifies which entry it is and the value is the offset in the file where you can find the entry
- updating the dictionary is quite easy
- Bitcask with RIAK does that. Downside is that the keys have to live in RAM memory
- For writes, we mostly append to a log file - log files grow, so they need to be segmented
- We handle the size of our log files by segmenting, compacting and merging log files
- Segmenting involves breaking the log file into multiple such files 
- Compacting involves getting rid of the duplicate parts from our log
- Merging involves creating a new log file with the contents of several (where we keep only the last instance of the key)

In a real database implementation, we have to deal with several other issues such as :
    - the file format/ CSVs or JSONs are great for humans, but bytes are more easily storeable
    - Deleting records is handled by appending a `Tombstone`. The `Tombstone` tells the merging process to get rid of the entries older than the tombstone.
    - If the DB is restarted, the contents in memory are erased. We need fast ways of restoring the database, and reading all the segments to recreate the state in memory can be costly
    - We can have partially written records when a crash occurs - the content will be corrupted - checksums are used to this extent
    - It's common to have only 1 writer thread and have multiple reader threads to not have the database in an inconsistent state ( concurrency control)

Append only logs and hash tables are okay because
    - appendingb data is a sequential op and this is faster than random writes
    - concurrency and crash recovery are easier if the log is immutable
    - merging old segments makes sure you don't get fragmentation

There are disadvantages:
    - you cannot make the hashmap perform well if you have several different keys
    - you cannot do range scans

## SSTables and LSM-Trees

- Key value pairs should be sorted by key
- This is a Sorted String table
- Each key should appear only once (the compaction process can make sure of that )
- It's easier to merge segments now because we can apply merge sort ( for example)
- Only write the keys from the latest segment
- You no longer need to keep indexes in memory - you only need to know a handful of such indexes, and then you can deduce where the other might be
- Since values are sorted, you can better compress the data before writing it to disk - keep a sparse in memory index

## Constructing and maintaing SSTables

- It's easier to maintain a sorted structure in RAM.
- Many options such as Redblack trees or AVL trees (read back in sorted order)

You can achieve an SSTable by
    - Keeping elements in memory up until they get to about 4 MB
    - When the memtable gets bigger, write to disk
    - To serve a read, look in memory, then in the next oldest disk segment and so on
    - Run a compacting process in the background

To achieve some protection in case of a crash, write a log of the latest memtable to disk. This is to recover the memtable. When the memtable is written to the SSTable file, remove the log.


## LSM Trees out of SSTAbles

- LevelDB, RockDB, Cassandra and HBase use LSM Trees
- LSM Trees are Log Structured Merge Trees
- Lucene (full text search used by ElasticSearch and Solr) uses a similar method for storing its `term dictionary`
- ?? didn't really describe method

## Performance optimizations

- Can use a bloom filter to make sure the key exists before fetching it
- Compaction can be done by Size or by Level ( LevelDb and RocksDB are Level compacted )
- In size tiered, we successively merge smaller SSTables into older and larger ones
- In leveled compaction, the key range is split into smaller SSTables and older data is moved into separate levels - compaction proceeds incrementally and uses less disk space
- LSM trees keep a cascade of SSTables that are merged in the background

## B-Trees

- Most widely used indexing structure
- Industry standard sicne 1980
- Standard index implementation in all databases

The implementation is as follows :
    - database is broken down into fixed size blocks ( pages)
    - ABout 4kb in size each
    - each page is identified using an address or a location and it allows pages to reference each other
    - the pointer references content on disk
    - Pages either hold references or actual keys - a page which contains individual keys is a leaf page
    - Typically, you try to add to the same page -if it succeeds, continue adding to that page, else, break up page into 2 smaller half-full pages
    - The B-Tree should remain balacned.
    - Most databases have a B-Tree that is 3 or 4 levels deep ( four levels with 4KB pages and a branching factor of 500 can store up to 256 TB )
    - Deletion is harder that insertion

To make BTrees reliable, it is common to include a Write Ahead Log 
Every BTree modification is written there. In case of a crash, the BTree can be recovered 
- The tree structure is protected with latches to ensure that reads find the BTree in a consistent state

## BTree optimizations

- Some DBs use a copy-on-write scheme instead of `WAL`s for crash protection
- save only part of the key instead of saving the entire key
- BTree find it difficult to keep data sequential on the disk - LSM trees don't struggle with that since they rewrite the data Often
- Fractal trees borrow some log-structured ideas to reduce disk seeks

## Btrees versus LSM Trees

- lsm trees are faster for writes and slower for reads / btrees are the opposite
- you cannot say which one would fare better based on this alone though

## Advantages of LSM Trees

- Btrees write every piece of data once to the `WAL` and once to the tree page - some overhead
- log structuresd indexes rewrite data multiple times during compaction and merging and this is an issue for SSDs (`write amplification` - many rewrites to disk of the DB content during its lifetime)
- LSM trees have higher write throughputs
- LSM trees can be compressed better and produce smaller files on disk
- BTrees produce quite some fragmentation / LSM trees with their rewrites reduce fragmentation
- On many SSDs, random writes are turned into sequential writes to reduce the impact of the write pattern

## Disadvantages

- Background threads running compaction can reduce the performance of reads
- Higher percentiles especially affected 
- BTree response times can be more predictable
- Compaction requires more and more disk bandwidth
- Compaction might not be able to keep up with rate of writes
- SStables don't throttle writes, so you need to monitor this
- In SSTables, keys exist in multiple places ( in Btrees, they don't)

- Gotta test empirically which one is better - not really an easy answer ( BTrees have stood the test of time though )

## Other indexing structures

- So far we discussed only primary keys
- You can have secondary indexes via CREATE INDEX 
- Secondary indexes can have dupes
- Both BTrees and Log structures indexes can be used as secondary indexes

## Storing values withing the index

- The key is what we search for
- The value can be an actual row or a reference to a row which is stored elsewhere
- Reffed rows would be stored in a heap file
- Heap files common with secondary indexes to keep track of data only once
- Clustered indexes store row data in the index
- Nonclustered indexes sotre references to the data
- Covering indexes are a compromis3e and they store some columns
- Clustering and covering indexes speed up reads but require additional storage :(

## Multi column indexes

- Concatenated indexes are the most common
- Sort by first, then sort by second column  (Phonebook example)
- Last name - first name easy to find/ hard the other way around
- Range queries with latitude and longitude cannot be answered efficiently by BTrees or LSM trees

- Can translate bidimensional data into a space filling curve and then use a btree index 
- Can use RTrees ( POSTGis does that using posgres#s Generalized Search Tree indexing)
- Multidimensional indexes are not only for geolocations ( can be time and temperature for weather, can be RGB for product colors on an ecommerce website)
- With a unidimensional index, you filter on one column and then do a linear scan on the result.
- 2D indexes exist that narrow down both at the same time ( HyperDex)

## Full text search and fuzzy indexes

- Mispelled words require fuzzy querying
- Full text search allow searches for a word to be expanded to include synonyms or ignore gramattical variations (GIN and Trigrams)
- Lucene is able to search within a certain edit distance ( an edit distance of 1 means 1 removal, replacement or addition)
- In Lucene, we have a finiote state automaton over the characters similar to a Trie/ this is tranformed to a Leventshtein Automaton
- Othe rfuzzy search techniques include ML and document classification

## Keeping everything in memory

- There are inmemory DBs such as Memcached and Redis
- VoltDB, MemSQL and Oracle TimesTen are in memory databases with a relational model
- RAMCloud is an open soruce in memory key value store with durability (log structured approach )
- Redis and Couchbase provide weak durability by writing to disk Async
- These structures are faster because they avoid encoding data in a way in which it is writable to Disk
- Can store data sets larger than the available memory (the technique is called anti-cachinga and we evict the latest unused entry) 
- Indexes still need to fit entirely in memory
- Might change if NVMs are more widely adopted

## Transaction processing or analytics

- Online transaction processing (OLTPs) - these provide business critical infrastructures
- Databases are also used for data analysis - these are OLAPs
- OLAPs are typically separate from OLTPs because you don't wanna hammer business critical infrastructures with business intelligence logic - queries can be quite heavy

- OLAPs and OLTPs have different patterns
- (Referecence table on Page 91 - table 3-1)
- OLTPs are supposed to be highly available
- Data is dumped from OLTPS to OLAPs via a process known as Extract, transofrm, load ( see Figure 3-8 on page 92)
- OLAPs are typically used by larger scale companies
- OLAPs are good at answering analytic queries

## Divergence between OLTPs and OLAPs

- Both use SQL to query data
- Internals are different
- SAP HANA, Teradata, Vertical, ParAccel are such OLAP solutions
- Apache Hive, Facebook PResto, Spark SQL are open source solutions

## Stars and Snowflakes

- Data warehouses use something called `Star schemas`
- the center of the schema is a `fact` table which has many outgoing references to other tables
- Fact tables contain tons of data of transaction history
- Snowflake schemas are more normalized, but star schemas are preferred because they're easier to work with 

## Column oriented storage

- SELECT * queries are often not needed / we mostly return a bunch of columns
- Store columns instead in files 
- OLTPs typically store data in a row oriented fashion
- OLTPs would read each row and then parse for the relevant column - can be slow
- in OLAPs, if you need the row 23, just assemble entry number 23 from all column files

## Column compression
- Since data for the first few columns is tyically sorted, we can compress these better 
- can use bitmap encoding

## Memory bandwidth and vectorized processing

- Data warehouse queries scan over milliopns of rows - bottleneck is getting data from disk
- loads of techno bable in here with SIMD and other stuff

## Several sort orders

- Sicne we need data to be replicated for resilience, C-Store stores data with different sort orders on replicas

## Writing to column oriented storage

- BTrees are not good for that, byt LSM Trees are
- Vertica does this

## Aggregation: Data Cubes and Materialized views

- Can be wasteful to redo aggregate functions such as COunt, Min, MAx, Avg
- Store this aggregated data into a materialized view
- The results of some query
- Materialized views need to be updated.
- A common case of a materialized view is a Data Cube or OLAP cube
- God knows what this is

## Summary

- OLTPS are user facing and need to service a huge volume of requests
- OLAPS are analyst facing and these need to service a lower number of requests which are more computationally intensive
