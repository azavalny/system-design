# Batch Processing
Processing on immutable, fixed size data

**Map Reduce:**
1. Break input files into batches/records
2. `mapper(input record) => key, value`
3. Sort records by key
4. `reducer(key, value)=> output`

* Utilize parallelism on commodity machines where each program processes one record at a time
* Partitioned on mapping and reducing tasks

### Map Reduce Workflows
Workflow - chain of Map Reduce jobs like a linux pipe: `MR_1 | MR_2 | ...`
* Store intermediate states of computation which when replicated is overkill and waste of resources

**Sort-merge join** 
2 mappers map different columns to the same key with the reducer combining the values of both where reducer partitions based on properties like even/odd ID

**Map-side join**
Data sent directly to mapper and outputted. Making assumption that input is already sorted and small

Hadoop ETL - Raw data from distributed filesystem gets Map-Reduced into relational data to be stored in a warehouse for OLAP queries

Pre-empted - terminated to free resources

**Dataflow Engine** - Generalized Map Reduce workflow as one job e.g. Spark
* Process one record at a time on a single thread with parallelizing partitioned inputs
* Outputs of one function as inputs to another like Linux pipes
* Reduces intermediate state memory compared to regular Map Reduce


# Stream Processing
Data incrementally available over time like lazy evaluation

**Event/Message** - record at a point in time 
* Processed as infinite streams incrementally processed grouped as topics

Stream Processor - consumes input streams as read only and writes output in append only

Continual procesing - Since polling a database becomes expensive and with overhead for each poll, when you need fewer delays and fast processing, it's better to notify consumers/subscribers when new events appear

> The more often you poll, the lower % of requests return new events which creates overhead


Webhook - producer making HTTP or RPC request to service on a callback URL

**## Message Queue** - Producer produces events that the consumer consumes and removes from the Queue e.g. RabbitMQ, AWS SQS
* Consumers are asynchronous and decoupled from producers
* Consumers can be used to load balance work by consuming and removing tasks

**## Message Log** - Append only log of events partitioned like a database e.g. Kafka, AWS Kinesis, Azure Event Hub
* Uses monotonically increasing offset for each partition to keep track of latest message that was processed, and for replaying messages easily
* Retention policy set to remove old messages via their timestamp
* "Fan out" - have one producer send same message to each consumer for their own topic


| Message Queue | Message Log |
| -------- | -------- |
| Parallelize message processing with multiple consumers | High throughput, fast processing |
| Order dosen't matter | Order matters |


Uniqueness Pattern for log based messaging:
1. New request appended to log in a partition
2. Stream processor sequentially reads requests in the log and uses a database to keep track of previously procesesed requests and reject duplicates for idempotent processing

Comes with data integrity and timeliness is how long consumer waits for message:
1. Atomic writes as they're wrapped into one message
2. Deterministic state updates and replaying states
3. Ability for idempotent operations using hashing and IDs
4. Immutable messages allow for system to recover easily from bugs


Change Data Capture - stream of all data changes to a database
* Replay log to get a copy of database state in another system

Log compaction - removing overwritten log records and keeping the most recent updates which gives you a full copy of a database
* Database is a cache of the latest records of a log with the latest values of each record and index value from log

Event Sourcing - changes in application level history as immutable events like user interactions with a website

Tip for logging timestamps log:
1. Time of event on local device
2. Time event was sent to server on local device
3. Time event was recieved from the server

2-3 gives device-server offset and apply to event timestamp


### Stream Joins:

1. Stream-stream join - 2 events joined on session ids 

2. Stream-table join - join event with entry from a database table


Microbatching - split stream into small one second chunks

Idempotent processing - event processed twice dosen't produce any side effects like duplicate data
* Ensured using hashing or indexed ids stored in metadata 
* Avoid partial output
