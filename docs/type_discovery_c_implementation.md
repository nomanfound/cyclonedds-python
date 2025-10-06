# Type Discovery C Implementation Documentation

## Overview

This document describes the C/C++ implementation for type discovery functionality that uses DCPSPublication and DCPSSubscription builtin topics to obtain type information and generate IDL string representations.

## Background

The current Python implementation of type discovery (`cyclonedds/tools/cli/discovery/main.py::type_discovery`) performs the following steps:

1. Creates a DomainParticipant
2. Subscribes to DCPSPublication and DCPSSubscription builtin topics
3. Collects type information including TypeIdentifier from discovered endpoints
4. Uses `get_types_for_typeid()` to fetch TypeObject via XTypes type discovery
5. Converts TypeObject to Python classes using `XTInterpreter`
6. Generates IDL string from Python classes using `IdlType.idl()`

## Proposed C Implementation

### Architecture

The implementation consists of two main components:

#### 1. Type Information Retrieval Function (`ddspy_get_endpoint_typeinfo`)

**Purpose:** Retrieve type information from a DCPSPublication or DCPSSubscription endpoint.

**Signature:**
```c
static PyObject *ddspy_get_endpoint_typeinfo(PyObject *self, PyObject *args)
```

**Parameters:**
- `endpoint`: DcpsEndpoint object containing endpoint information
- `participant`: DomainParticipant entity reference
- `timeout`: Timeout duration for type object retrieval

**Returns:**
- Dictionary containing:
  - `type_id`: Serialized TypeIdentifier
  - `type_name`: Type name string
  - `topic_name`: Topic name string
  - `type_object`: Serialized TypeObject (if available)

**Implementation Steps:**
1. Extract TypeIdentifier from endpoint
2. Call `dds_get_typeobj()` to fetch TypeObject from participant
3. Serialize both TypeIdentifier and TypeObject
4. Return as Python dictionary

#### 2. IDL Generation Function (`ddspy_typeobj_to_idl`)

**Purpose:** Convert a TypeObject to its IDL string representation.

**Signature:**
```c
static PyObject *ddspy_typeobj_to_idl(PyObject *self, PyObject *args)
```

**Parameters:**
- `type_id_buffer`: Serialized TypeIdentifier
- `type_obj_buffer`: Serialized TypeObject
- `typemap_dict`: Dictionary of TypeIdentifier -> TypeObject mappings for dependencies

**Returns:**
- String containing IDL representation

**Implementation Steps:**
1. Deserialize TypeIdentifier and TypeObject
2. Process nested type dependencies from typemap
3. Generate IDL string following OMG IDL 4.2 specification
4. Handle structs, unions, enums, bitmasks, typedefs, sequences, arrays

### Data Flow

```
DCPSPublication/Subscription Endpoint
    |
    v
ddspy_get_endpoint_typeinfo()
    |
    +-- Extract TypeIdentifier
    +-- Call dds_get_typeobj()
    +-- Serialize data
    |
    v
Python Layer (collect all type dependencies)
    |
    v
ddspy_typeobj_to_idl()
    |
    +-- Deserialize TypeObject(s)
    +-- Traverse type structure
    +-- Generate IDL declarations
    +-- Format output string
    |
    v
IDL String Output
```

## Type Support Details

### TypeObject Processing

The TypeObject structure contains:
- **CompleteTypeObject**: Full type definition with annotations, member names, etc.
- **MinimalTypeObject**: Reduced type definition with hash-based identifiers

For IDL generation, we prefer CompleteTypeObject when available.

### IDL Generation Rules

1. **Module Scoping**: Types are scoped within modules (e.g., `module Foo { struct Bar {}; };`)
2. **Struct Definition**: 
   ```idl
   struct Name {
       Type1 member1;
       Type2 member2;
   };
   ```
3. **Union Definition**:
   ```idl
   union Name switch(DiscriminatorType) {
       case Label1: Type1 member1;
       case Label2: Type2 member2;
   };
   ```
4. **Enum Definition**:
   ```idl
   enum Name {
       VALUE1,
       VALUE2
   };
   ```
5. **Type Dependencies**: All referenced types must be defined before use

### Error Handling

- Return NULL with Python exception on:
  - Invalid TypeIdentifier/TypeObject format
  - Missing type dependencies in typemap
  - Memory allocation failures
  - DDS API errors

## Integration with Existing Code

### C Layer (`clayer/pysertype.c`)

Add new functions alongside existing type discovery code:
- `ddspy_get_endpoint_typeinfo` - new function
- `ddspy_typeobj_to_idl` - new function

These will be added in the `#ifdef DDS_HAS_TYPE_DISCOVERY` section.

### Python Layer

Create new module `cyclonedds/type_discovery_c.py`:
```python
from cyclonedds._clayer import ddspy_get_endpoint_typeinfo, ddspy_typeobj_to_idl

def get_idl_from_endpoint(participant, endpoint, timeout):
    """Get IDL string from a DCPSPublication or DCPSSubscription endpoint."""
    # Collect type information
    typeinfo = ddspy_get_endpoint_typeinfo(endpoint, participant._ref, timeout)
    
    # Build typemap with dependencies
    typemap = {}
    to_resolve = [typeinfo['type_id']]
    
    while to_resolve:
        tid = to_resolve.pop()
        # Get typeobj for tid...
        # Add to typemap
    
    # Generate IDL
    idl_string = ddspy_typeobj_to_idl(
        typeinfo['type_id'],
        typeinfo['type_object'],
        typemap
    )
    
    return idl_string
```

## Testing Strategy

1. **Unit Tests**: Test individual C functions with known TypeObjects
2. **Integration Tests**: Test full flow from endpoint discovery to IDL generation
3. **Compatibility Tests**: Ensure generated IDL matches Python implementation output
4. **Edge Cases**:
   - Circular type dependencies
   - Missing type information
   - Complex nested structures
   - All primitive types
   - Arrays and sequences with bounds

## Performance Considerations

- C implementation should be significantly faster than Python for IDL generation
- Minimize memory allocations by reusing buffers where possible
- Use streaming approach for large type definitions
- Cache type information to avoid redundant network requests

## Future Enhancements

1. Support for annotations (@key, @optional, etc.)
2. Pretty-printing with indentation control
3. Option to generate C or C++ bindings instead of IDL
4. Incremental IDL generation for partial type information
5. Type validation against IDL specification

## References

- OMG IDL 4.2 Specification
- DDS XTypes 1.3 Specification
- CycloneDDS Type Support Documentation
- Existing Python implementation in `cyclonedds/dynamic.py` and `cyclonedds/tools/cli/idl.py`
