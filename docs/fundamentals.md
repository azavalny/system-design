# Fundamentals

Core vocabulary and the basic structure for organizing software systems.

## Key Vocabulary

- **Throughput** - # of requests processed / time
- **Latency** - how long a request takes to be handled
  - Combination of wait/idle time for other resources and processing time of your programs
  - **Response time** is what the client sees: latency + network delay to transport the result to the user
- **Idempotence** - send same request twice, get same result with no side effects
- **Eventual consistency** - A change in the data in one location will eventually be updated in every other location, but reads from other locations may not yet have the updated value

## Organizing Software

It's best to organize software into:

- **Client** - part of backend where the request is handled
- **Services** - process request
- **Resources** - databases that services query from

That way the client doesn't have to directly access resources and everything can be independent.
