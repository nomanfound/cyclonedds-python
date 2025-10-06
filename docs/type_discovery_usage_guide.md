# Type Discovery from Endpoints - Usage Guide

This guide explains how to use the type discovery functions to obtain type information and IDL representations from DCPSPublication and DCPSSubscription builtin topics.

## Overview

The `type_discovery_c` module provides functions to:

1. Extract type information from discovered endpoints (publishers/subscribers)
2. Generate IDL string representations of discovered types
3. Process multiple endpoints efficiently

## Prerequisites

- CycloneDDS must be compiled with `ENABLE_TYPE_DISCOVERY=ON`
- The discovered endpoints must support XTypes (have `type_id` information)

## Basic Usage

### 1. Discovering Types from Publications

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

# Create a domain participant
dp = domain.DomainParticipant()

# Create a reader for the DCPSPublication builtin topic
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

# Read publications
publications = pub_reader.take(N=10)

# Get IDL for each publication
for pub in publications:
    if pub.type_id is not None:
        try:
            idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
            print(f"Topic: {pub.topic_name}")
            print(f"Type: {pub.type_name}")
            print(idl)
            print()
        except Exception as e:
            print(f"Failed to get IDL for {pub.topic_name}: {e}")
```

### 2. Discovering Types from Subscriptions

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()

# Create a reader for the DCPSSubscription builtin topic
sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)

# Read subscriptions
subscriptions = sub_reader.take(N=10)

# Get IDL for each subscription
for sub in subscriptions:
    if sub.type_id is not None:
        idl = get_idl_from_endpoint(dp, sub, util.duration(seconds=1))
        print(f"Subscription on topic: {sub.topic_name}")
        print(idl)
```

### 3. Batch Discovery from Multiple Endpoints

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import discover_types_from_endpoints

dp = domain.DomainParticipant()

# Read from both publication and subscription builtin topics
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)

publications = pub_reader.take(N=100)
subscriptions = sub_reader.take(N=100)

# Combine all endpoints
all_endpoints = publications + subscriptions

# Discover all unique types
discovered_types = discover_types_from_endpoints(
    dp, 
    all_endpoints, 
    util.duration(seconds=2)
)

# Print discovered types
for topic_name, (type_name, idl) in discovered_types.items():
    print(f"Topic: {topic_name}, Type: {type_name}")
    print(idl)
    print("-" * 60)
```

## Advanced Usage

### 1. Getting Type Information Without IDL Generation

If you only need the TypeObject without generating IDL:

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_endpoint_typeinfo

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

publications = pub_reader.take(N=1)
if publications and publications[0].type_id is not None:
    typeinfo = get_endpoint_typeinfo(
        dp, 
        publications[0], 
        util.duration(seconds=1)
    )
    
    # typeinfo is a dictionary with:
    # - 'type_id': bytes (serialized TypeIdentifier)
    # - 'type_object': bytes (serialized TypeObject)
    # - 'topic_name': str
    # - 'type_name': str
    
    print(f"Retrieved TypeObject for {typeinfo['type_name']}")
    print(f"Type ID size: {len(typeinfo['type_id'])} bytes")
    print(f"Type Object size: {len(typeinfo['type_object'])} bytes")
```

### 2. Filtering Endpoints by Topic Pattern

```python
import re
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

# Read all publications
publications = pub_reader.take(N=100)

# Filter by topic name pattern
topic_pattern = re.compile(r'^MyApp.*')

for pub in publications:
    if topic_pattern.match(pub.topic_name) and pub.type_id is not None:
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        print(f"Topic: {pub.topic_name}")
        print(idl)
```

### 3. Continuous Type Discovery

Monitor for new types being discovered:

```python
import time
from cyclonedds import domain, builtin, util, core
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

# Create read condition for new samples
condition = core.ReadCondition(
    pub_reader,
    core.SampleState.NotRead | core.ViewState.Any | core.InstanceState.Alive
)

discovered_topics = set()

print("Monitoring for new types...")
try:
    while True:
        publications = pub_reader.take(N=10, condition=condition)
        
        for pub in publications:
            if pub.topic_name not in discovered_topics and pub.type_id is not None:
                discovered_topics.add(pub.topic_name)
                
                print(f"\nNew type discovered!")
                print(f"Topic: {pub.topic_name}")
                print(f"Type: {pub.type_name}")
                
                try:
                    idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
                    print(idl)
                except Exception as e:
                    print(f"Failed to get IDL: {e}")
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopped monitoring")
```

## Error Handling

### Common Errors and Solutions

#### 1. Type Discovery Not Enabled

```python
from cyclonedds.core import DDSException

try:
    idl = get_idl_from_endpoint(dp, endpoint, timeout)
except DDSException as e:
    if "not compiled with type support" in str(e):
        print("CycloneDDS was not compiled with ENABLE_TYPE_DISCOVERY=ON")
```

#### 2. Endpoint Without Type ID

```python
from cyclonedds.type_discovery_c import get_idl_from_endpoint

for pub in publications:
    if pub.type_id is None:
        print(f"Skipping {pub.topic_name}: no type_id (XTypes not enabled)")
        continue
    
    try:
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        print(idl)
    except ValueError as e:
        print(f"Error: {e}")
```

#### 3. Timeout Issues

```python
from cyclonedds import util

# Use longer timeout for complex types
timeout = util.duration(seconds=5)

try:
    idl = get_idl_from_endpoint(dp, endpoint, timeout)
except RuntimeError as e:
    if "timeout" in str(e).lower():
        print("Type discovery timed out - try increasing timeout")
    else:
        print(f"Error: {e}")
```

## Performance Considerations

### 1. Batch Processing

When discovering types from many endpoints, use `discover_types_from_endpoints()` instead of calling `get_idl_from_endpoint()` individually:

```python
# ❌ Slower - individual calls
for endpoint in endpoints:
    idl = get_idl_from_endpoint(dp, endpoint, timeout)

# ✅ Faster - batch processing
discovered = discover_types_from_endpoints(dp, endpoints, timeout)
```

### 2. Caching Results

Cache discovered types to avoid redundant network requests:

```python
type_cache = {}

def get_cached_idl(dp, endpoint, timeout):
    topic_name = endpoint.topic_name
    
    if topic_name not in type_cache:
        type_cache[topic_name] = get_idl_from_endpoint(dp, endpoint, timeout)
    
    return type_cache[topic_name]
```

## Integration with Existing Code

### Using with cyclonedds typeof Command

The implementation follows the same pattern as the `cyclonedds typeof` command:

```bash
# Command line
$ cyclonedds typeof MyTopic

# Python equivalent
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

for pub in pub_reader.take(N=100):
    if pub.topic_name == "MyTopic" and pub.type_id is not None:
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        print(idl)
        break
```

### Using with Dynamic Type Support

Combine with `cyclonedds.dynamic` for full dynamic typing:

```python
from cyclonedds import domain, topic, sub, util
from cyclonedds.dynamic import get_types_for_typeid
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

for pub in pub_reader.take(N=10):
    if pub.type_id is not None:
        # Get IDL representation
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        print(f"IDL for {pub.topic_name}:")
        print(idl)
        
        # Get Python type for runtime use
        datatype, nested_types = get_types_for_typeid(
            dp, pub.type_id, util.duration(seconds=1)
        )
        
        # Create topic and reader with discovered type
        tp = topic.Topic(dp, pub.topic_name, datatype)
        dr = sub.DataReader(dp, tp)
        
        # Read data
        samples = dr.read(N=10)
        print(f"Read {len(samples)} samples")
```

## Complete Example

Here's a complete example that ties everything together:

```python
#!/usr/bin/env python3
"""
Complete example of type discovery from endpoints.
"""

import time
from cyclonedds import domain, builtin, util, core
from cyclonedds.type_discovery_c import discover_types_from_endpoints


def main():
    # Create domain participant
    dp = domain.DomainParticipant()
    
    # Create readers for builtin topics
    pub_reader = builtin.BuiltinDataReader(
        dp, builtin.BuiltinTopicDcpsPublication
    )
    sub_reader = builtin.BuiltinDataReader(
        dp, builtin.BuiltinTopicDcpsSubscription
    )
    
    print("Discovering types on the network...")
    print("Waiting 2 seconds for discovery...")
    time.sleep(2)
    
    # Read all endpoints
    publications = pub_reader.take(N=100)
    subscriptions = sub_reader.take(N=100)
    all_endpoints = publications + subscriptions
    
    print(f"\nFound {len(publications)} publications")
    print(f"Found {len(subscriptions)} subscriptions")
    
    if not all_endpoints:
        print("\nNo endpoints discovered.")
        print("Make sure other DDS applications are running.")
        return
    
    # Discover types
    print("\nDiscovering types...")
    discovered = discover_types_from_endpoints(
        dp, 
        all_endpoints, 
        util.duration(seconds=2)
    )
    
    if discovered:
        print(f"\nDiscovered {len(discovered)} unique types:\n")
        
        for topic_name, (type_name, idl) in discovered.items():
            print("=" * 70)
            print(f"Topic: {topic_name}")
            print(f"Type: {type_name}")
            print("-" * 70)
            print(idl)
            print()
    else:
        print("\nNo types could be discovered.")
        print("This may happen if:")
        print("  - XTypes is not enabled in the endpoints")
        print("  - Type discovery is not compiled in CycloneDDS")


if __name__ == "__main__":
    main()
```

## See Also

- [CycloneDDS Python API Documentation](https://cyclonedds.io/docs/)
- [Type Discovery C Implementation Details](type_discovery_c_implementation.md)
- [DDS XTypes Specification](https://www.omg.org/spec/DDS-XTypes/)
- `cyclonedds.dynamic` module for runtime type discovery
- `cyclonedds.tools.cli.typeof` command-line tool
