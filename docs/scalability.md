# Scalability

Scaling strategies, microservices, event-driven architecture, and stateful vs stateless tradeoffs.

## Scalability

- **Horizontal scaling** - more of the same machine to handle more load
  - Cost grows linearly
  - Software has to support multi-machine instances and coordinate data between them
- **Vertical scaling** - upgrading hardware
  - Cost grows nonlinearly
  - Committing to the machine you buy

To scale a system you need:

1. **Decentralization** - specialized workers
2. **Independence** - of workers to take advantage of concurrency

Monoliths by definition are anti-patterns for scalability.

### Modularity

**Modularity** is breaking business logic down into specialized functions/services with loosely coupled modules and decoupled services.

To make a system scalable, you have to make it decentralized with independent components:

- Cache frequently read and rarely modified data to reduce load on the backend
- Use asynchronous and event-driven processing for distributing load over time
- Vertically partition systems into independent, stateless, replicated services
- Shard and replicate data
- Use load balancers to distribute load evenly
  - Discovery service to offload tracking healthy IP addresses away from load balancer
- DNS as a load balancer at a global scale

## Microservices

Microservices are vertically partitioned services and databases that make your software highly scalable, typically leading to eventual consistency.

- Services developed and deployed independently (for each business vertical) with separate database and schema for each service
  - Allows frequent deployment of new features for users
- Tradeoff exists between independence and reusability of components:
  - Prefer separate schemas and services for each business vertical
  - Avoid reusable libraries except utilities to reduce coupling

### Microservice Distributed Transactions

- Don't reuse libraries except utilities to avoid inter-service dependencies
- **Compensating transactions / saga pattern** means you roll back the entire workflow if any part fails
  - Apology transaction to fix or undo previous writes
  - Tradeoff between number of apologies for inconsistencies in data integrity and performance + availability of a system
- Older approach is **2-phase commit (2PC)**:
  - Commit requires all services to vote
  - Poor fit for microservices compared to compensating transactions

### Sync vs Async

- Use **synchronous** processing for immediate responses and read queries
- Use **asynchronous** processing for write queries and where deferred responses are okay

## Event-Driven Architecture

Event-driven architecture: producers publish events to a router/broker/message queue and consumers consume them.

- Producer and consumer services being decoupled allows them to scale, be developed, and deployed independently
- Transactions are done async and the database may be polled regularly in case services go down
- If a transaction step as part of an event fails, new undo events are created to revert changes to the database

## Stateful vs Stateless Web Apps

- **Stateful** web applications have data in-memory and require low latency
- **Stateless** web applications store data in caches leading to higher scalability than stateful at the expense of higher latency
  - Store session data in caches like Redis and/or client-side cookies, or server shared cache
