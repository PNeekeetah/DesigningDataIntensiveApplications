# Stream processing

- derived data can be obtained by rerunning the batch process
- can be used to create indexes, recommendation system and analytics
- input was bounded, so we could tell when it finishes
- `last` key in a stream can be the lowest one, what to do ? 
- a lot of unbound data arrives and it is processed once at the end of the day or at the end of every hour
- batch processors artificially divide this data into timeslots
- changes in input are reflected slowly ( every day or hour, depending on the increment)
- Reduce the time slices to a second or less!#
- Streams are data that is made available over time / you get it in filesystem APIs, TCP conns, AV 

## Transmitting event streams

- for batch processing, inputs and outputs are files 
- In stream processing, we don't have `records` - we have `events`
- contains details of something that happened together with a timestamp from a Time of day clock
- might be a user action, might be a machine reading, might be a CPU utilization metric - web server logs are events !
- events can be a string, a JSON or binary
- you can write it to a file or in the database
- you can send it over a network to another node
- An event can be produced by one producer and consumed by multiple consumers ( subscribers )
- events are grouped into a topic ( or stream ) - batch processes are grouped in files
- files or databases are enough to connect producers and consumers / each consumer polls the the datastore for updates since the last time it checked
- polling can become expensive the more you poll your datastore / better for consumers to get notifications
- databases aren't well adapted for delivering notifications ( we have triggers, but they're limited ) 
- we got specialized tools for delivering notifications

## Messaging Systems

- A common approach for notifying consumers is to use a messaging system - messages are pushed to consumers
- UNIX pipes allow only one producer and consumer
- messaging systems expand on this and allow multiple consumers 

- many approaches exist for passing around messages, and none is the correct one
- Keep 2 questions in mind
    1. If producers produce faster than cosnumers can consume, what happens with the data ? 
        - drop messages
        - buffer in a queue
        - apply backprressue ( block producers ) - unix pipes and TCP do this
    1a. If queues are filled up, does the system crash ? do we write to disk ? 

    2. What happens if nodes crash or go offline ? 
        - do you write to disk ? 

- If you lose some messages, you can likely get higher throughput and lower latency
- how important losing messages is depends on the application  ( sensor readings are fine to be dropped, but banking events might not be !)
- Batch processing has a strong reliability guarantee in that it retries dropped events

## Direct messaging from producers to consumers

- some messaging systems use direct network communication without intermediary nodes
-  UDP multicast is used in the financial industry - app level protocols can recover lost UDP messages
- ZMQ and nanomsg implement publish/subscribe over IP multicast or TCP
- StatsD and Brubeck use UDP messaging 
- These work well, but they require the application to be aware that messages might be lost
- faults can be tolerated if they're limited
- if a consumer is offline, you can retry sending a message - but if a producer dies, buffered messages might be lost ( eg the ones it had to retry )

### Message brokers

- message queues (brokers ) are an alternative
- database optimized for handling message streams
- it runs as a server and producers and consumers connect to it
- brokers can tolerate consumers and producers that come and go - durability is put on the broker
- brokers can keep data in the memory or on durable storage / when consumers are slow, brokers store these messages (instead of applying backpressure )
- queueing means that consumers are async - producers get an acknowledgement that the message was received, but then the consumers might get these messages later


### Message brokers compared to databases

- message brokers can participate in 2PC using Xtended Arch
- they are similar to DBs, but there are some differences
    1. brokers delete messages once they're read
    2. individual messages might take longer to process if they're queued up for a long time
    3. dbs support secondary indexes, brokers have a way to subscribe to a subset of topics
    4. brokers don't support arbitrary data querying, but notify consumers of changes

- These are traditional views on message brokers and they're implemented in software like RabbitMq and ActiveMQ (to name a few)

### Multiple consumesr

- if multiple consumers read messages from the same topic, we have the following patterns:

    1. Load balancing - each message is delivered only to one of the consumers such that consumers balance the load - process is paralelized
    2. Fan out - each message gets delivered to all consumers 

- See figure 11-1 on page 467 (445 physical copy)
-  you can combine these patterns

### Acknowledgements and redelivery

- Consumers may crash at any point (before receiving the message, whilst processing it or before responding)
- Producers receive ACKs from consumers - they can remove the message from the queue like this
- Producers deliver the message to another consumer if it doesn't get ACKed
- when combined with load balancing, redelivery has an interesting effect on message ordering ( see figure 11-2 on page 468 / 446 physical copy)
- even if you try to preserve the order, when LB is involved, messages get re-arranged

## Partitioned logs

- sending packets is a transient operation that should leave no trace
- even when brokers durably write messages, they still end up getting deleted
- DBs take the opposite approach - everything is there forever
- processing messages from a broker is a destructive process - you cannot rerun the operations (same way you would play around with processing)
- adding consumers at a latter point in time means that they don't get to see previous results

- Why not combine durable message storage and low latency notifications ? ( this is what log based message brokers are )

### Using logs for message storage 

- logs are append only message storage mediums 
- producers append messages to a log and consumers consume the log (e.g. `tail -f`)
- for higher throughput, you need to scale the log - it should be partitioned
- different partitions can live on different machines
- within each partition, the broker assigns a monotonically increasing sequeunce number (or offset ) to every message 
- no ordering guarantees across partitions
- See figure 11-3 (page 470 / page 448 physical copy)
- kafka, amazon kinesis streams are log based message brokers
- even if these write messages to disk, they are able to achieve high throughputs by partitioning across multiple machines and fault tolerance by replicating messages 

### Logs compared to traditional messaging

- log based messaging supports fanout because messages can be read non-destructively
- for load balancing, the broker can assign entire partitions to nodes in the consumer group
- each client consumes all the messages it has been assigned from that partition

- This approach has downsides :
    1. number of nodes can be at most the number of log partitions
    2. If a single message is slow to process, the queue is held up ( head-of-line blocking )

### Consumer offsets

- Consuming a partition sequentially makes it easy to keep track of what was consumed 
- All messages with offset lower than the consumers have been processed / all with greater offset were not seen
- broker doesn't need to keep track of acknowlegdements/ it just records consumer offsets
- less bookkeeping, higher throughput !

- the offset is similar to the log sequence number in a single -leader database replication
- broker acts as a leader, consumers act like followers
- if a consumer dies halfway through, another consumer picks up from the last seen offset - it restarts altogether if the offset isn't known

### Disk usage space

- you can run out of disk space if you keep appending 
- old segments are deleted from time to time
- the consumer can fall so far behind that it starts reading from the deleted portion - the log is effectively a ring buffer (a large one) 6TB is 11 hours of buffered data at 150 MB/s
- log throughput on such systems remain the same! contrast this with messaging systems which only write to disk if they need to buffer data - for short queues, they're quick, but otherwise, they're slow

### When consumers cannot keep up with producers

- discussed 3 ways
- log based is just buffering with a large buffer
- you can monitor how far back a consumer has fallen and raise an alert for a human to fix the slow consumer
- even if one consumer is too slow, it won't affect other consumers
- you can experimentally consume production logs for development
- if a consumer crashes, the consumer offset reamins

### Replaying old messages

- when reading (compared to traditional messaging systems ), the only side effect is that the consumer offset is moved forwards
- you can start a copy of the consumer with yesterday's offset and write the output to a different location - you can repeat this !
- This makes log based messaging more similar to batch processing, allowing for more experimentation and easier recovery