# Type Discovery Quick Start Guide

Get started with type discovery from endpoints in just a few minutes!

## Installation

Ensure you have CycloneDDS Python installed with type discovery support:

```bash
pip install cyclonedds
```

Or build from source with type discovery enabled:

```bash
# Clone and build CycloneDDS with type discovery
git clone https://github.com/eclipse-cyclonedds/cyclonedds
cd cyclonedds && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install -DENABLE_TYPE_DISCOVERY=ON
cmake --build . --target install

# Install cyclonedds-python
export CYCLONEDDS_HOME="$(pwd)/../install"
pip install cyclonedds-python
```

## 5-Minute Tutorial

### 1. Discover Types on Your Network

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

# Create participant
dp = domain.DomainParticipant()

# Read from publication builtin topic
reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
pubs = reader.take(N=10)

# Get IDL for first publication
for pub in pubs:
    if pub.type_id is not None:
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        print(f"Topic: {pub.topic_name}")
        print(idl)
        break
```

### 2. Discover All Types at Once

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import discover_types_from_endpoints

dp = domain.DomainParticipant()

# Read all endpoints
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)

endpoints = pub_reader.take(N=100) + sub_reader.take(N=100)

# Discover all types
types = discover_types_from_endpoints(dp, endpoints, util.duration(seconds=2))

for topic, (typename, idl) in types.items():
    print(f"=== {topic} ({typename}) ===")
    print(idl)
    print()
```

### 3. Save IDL to Files

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import discover_types_from_endpoints
import os

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
endpoints = pub_reader.take(N=100)

types = discover_types_from_endpoints(dp, endpoints, util.duration(seconds=2))

# Create output directory
os.makedirs("discovered_types", exist_ok=True)

# Save each type to a file
for topic, (typename, idl) in types.items():
    filename = f"discovered_types/{typename}.idl"
    with open(filename, 'w') as f:
        f.write(idl)
    print(f"Saved {filename}")
```

### 4. Monitor for New Types

```python
import time
from cyclonedds import domain, builtin, util, core
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

# Track discovered topics
discovered = set()

print("Monitoring for new types (Ctrl+C to stop)...")

try:
    while True:
        pubs = reader.take(N=10)
        for pub in pubs:
            if pub.topic_name not in discovered and pub.type_id is not None:
                discovered.add(pub.topic_name)
                print(f"\nNew type discovered: {pub.topic_name}")
                try:
                    idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
                    print(idl)
                except Exception as e:
                    print(f"Error: {e}")
        time.sleep(0.5)
except KeyboardInterrupt:
    print(f"\nDiscovered {len(discovered)} types total")
```

## Common Patterns

### Pattern 1: Filter by Topic Name

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

# Only process topics starting with "MyApp"
for pub in reader.take(N=100):
    if pub.topic_name.startswith("MyApp") and pub.type_id is not None:
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        print(f"{pub.topic_name}:\n{idl}\n")
```

### Pattern 2: Compare Publication and Subscription Types

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint

dp = domain.DomainParticipant()
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)

# Get types from both sides
pub_types = {}
sub_types = {}

for pub in pub_reader.take(N=100):
    if pub.type_id is not None:
        pub_types[pub.topic_name] = get_idl_from_endpoint(
            dp, pub, util.duration(seconds=1)
        )

for sub in sub_reader.take(N=100):
    if sub.type_id is not None:
        sub_types[sub.topic_name] = get_idl_from_endpoint(
            dp, sub, util.duration(seconds=1)
        )

# Find matching topics
for topic in pub_types:
    if topic in sub_types:
        if pub_types[topic] == sub_types[topic]:
            print(f"✓ {topic}: Types match")
        else:
            print(f"✗ {topic}: Type mismatch!")
```

### Pattern 3: Generate Code from IDL

```python
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint
import subprocess
import tempfile

dp = domain.DomainParticipant()
reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)

for pub in reader.take(N=1):
    if pub.type_id is not None:
        idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.idl', delete=False) as f:
            f.write(idl)
            idl_file = f.name
        
        # Generate Python code using idlc
        print(f"Generating code from {pub.topic_name}...")
        subprocess.run(['idlc', '-l', 'py', idl_file])
        
        break
```

## Troubleshooting

### "CycloneDDS was not compiled with type support"

**Solution**: Rebuild CycloneDDS with `-DENABLE_TYPE_DISCOVERY=ON`

```bash
cd cyclonedds/build
cmake .. -DENABLE_TYPE_DISCOVERY=ON
cmake --build . --target install
```

### "Endpoint does not have type_id"

**Cause**: The endpoint doesn't support XTypes or type discovery is disabled.

**Solution**: Ensure your DDS applications are using XTypes-enabled types.

### Timeout errors

**Solution**: Increase the timeout:

```python
# Use longer timeout for complex types or slow networks
idl = get_idl_from_endpoint(dp, endpoint, util.duration(seconds=5))
```

### No endpoints discovered

**Cause**: No other DDS applications are running.

**Solution**: Start other DDS applications on your network:

```bash
# In terminal 1
cyclonedds subscribe SomeTopic

# In terminal 2 - run your discovery script
python my_discovery_script.py
```

## Next Steps

- Read the [Full Usage Guide](type_discovery_usage_guide.md)
- Check out [Implementation Details](type_discovery_c_implementation.md)
- Explore the [Example Script](../examples/type_discovery_example.py)
- Review the [Test Suite](../tests/test_type_discovery_c.py)

## Quick Reference

```python
# Main imports
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import (
    get_idl_from_endpoint,
    discover_types_from_endpoints,
    get_endpoint_typeinfo
)

# Create participant
dp = domain.DomainParticipant()

# Get readers for builtin topics
pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)

# Read endpoints
pubs = pub_reader.take(N=100)
subs = sub_reader.take(N=100)

# Get IDL from single endpoint
if pubs and pubs[0].type_id:
    idl = get_idl_from_endpoint(dp, pubs[0], util.duration(seconds=1))

# Batch discover types
all_endpoints = pubs + subs
types = discover_types_from_endpoints(dp, all_endpoints, util.duration(seconds=2))

# Get raw type info (advanced)
if pubs and pubs[0].type_id:
    info = get_endpoint_typeinfo(dp, pubs[0], util.duration(seconds=1))
    # info has: type_id, type_object, topic_name, type_name
```

Happy discovering! 🎉
