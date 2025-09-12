[![license](https://img.shields.io/github/license/kiarina/falkordb-py.svg)](https://github.com/kiarina/falkordb-py)
[![Release](https://img.shields.io/github/release/kiarina/falkordb-py.svg)](https://github.com/kiarina/falkordb-py/releases/latest)
[![PyPI version](https://badge.fury.io/py/kiarina-falkordb.svg)](https://badge.fury.io/py/kiarina-falkordb)

# kiarina-falkordb

> **⚠️ This is a temporary fork of [falkordb-py](https://github.com/FalkorDB/falkordb-py) with redis-py 6.x compatibility.**
>
> **Original work by the [FalkorDB team](https://github.com/FalkorDB/falkordb-py).**
>
> This fork will be deprecated once the [upstream PR](https://github.com/FalkorDB/falkordb-py/pull/123) is merged.

FalkorDB Python client with redis-py 6.x compatibility

## Installation
```sh
pip install kiarina-falkordb
```

## Differences from upstream

- ✅ Compatible with redis-py >= 6.0.0
- ✅ All original functionality preserved
- 🔄 Actively maintained until upstream compatibility is resolved

## Usage

### Run FalkorDB instance
Docker:
```sh
docker run --rm -p 6379:6379 falkordb/falkordb
```
Or use [FalkorDB Cloud](https://app.falkordb.cloud)

### Synchronous Example

```python
from falkordb import FalkorDB

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)

# Select the social graph
g = db.select_graph('social')

# Create 100 nodes and return a handful
nodes = g.query('UNWIND range(0, 100) AS i CREATE (n {v:1}) RETURN n LIMIT 10').result_set
for n in nodes:
    print(n)

# Read-only query the graph for the first 10 nodes
nodes = g.ro_query('MATCH (n) RETURN n LIMIT 10').result_set

# Copy the Graph
copy_graph = g.copy('social_copy')

# Delete the Graph
g.delete()
```

### Asynchronous Example

```python
import asyncio
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool

async def main():

    # Connect to FalkorDB
    pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)

    # Select the social graph
    g = db.select_graph('social')

    # Execute query asynchronously
    result = await g.query('UNWIND range(0, 100) AS i CREATE (n {v:1}) RETURN n LIMIT 10')

    # Process results
    for n in result.result_set:
        print(n)

    # Run multiple queries concurrently
    tasks = [
        g.query('MATCH (n) WHERE n.v = 1 RETURN count(n) AS count'),
        g.query('CREATE (p:Person {name: "Alice"}) RETURN p'),
        g.query('CREATE (p:Person {name: "Bob"}) RETURN p')
    ]

    results = await asyncio.gather(*tasks)

    # Process concurrent results
    print(f"Node count: {results[0].result_set[0][0]}")
    print(f"Created Alice: {results[1].result_set[0][0]}")
    print(f"Created Bob: {results[2].result_set[0][0]}")

    # Close the connection when done
    await pool.aclose()

# Run the async example
if __name__ == "__main__":
    asyncio.run(main())
```
