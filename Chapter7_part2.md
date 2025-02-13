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

