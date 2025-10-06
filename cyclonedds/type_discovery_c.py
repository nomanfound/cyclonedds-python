"""
 * Copyright(c) 2024 ZettaScale Technology and others
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Eclipse Distribution License
 * v. 1.0 which is available at
 * http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause
"""

from typing import Dict, Tuple, Optional
from collections import deque

from . import _clayer as cl
from .internal import feature_type_discovery
from .core import DDSException
from .domain import DomainParticipant
from .builtin_types import DcpsEndpoint
from .idl._typesupport.DDS.XTypes._ddsi_xt_type_object import TypeIdentifier, TypeObject
from .idl._xt_builder import XTTypeIdScanner
from .tools.cli.idl import IdlType


def get_endpoint_typeinfo(participant: DomainParticipant, endpoint: DcpsEndpoint, timeout: int) -> Dict:
    """
    Get type information from a DCPSPublication or DCPSSubscription endpoint.
    
    This function uses the C layer to efficiently retrieve TypeObject information
    from a discovered endpoint.
    
    Parameters
    ----------
    participant: DomainParticipant
        The domain participant to use for type discovery
    endpoint: DcpsEndpoint
        The endpoint (from DCPSPublication or DCPSSubscription builtin topic)
    timeout: int
        Timeout in nanoseconds for type object retrieval
        
    Returns
    -------
    dict
        Dictionary containing:
        - type_id: bytes - Serialized TypeIdentifier
        - type_object: bytes - Serialized TypeObject
        - topic_name: str - Topic name
        - type_name: str - Type name
        
    Raises
    ------
    DDSException
        If ENABLE_TYPE_DISCOVERY is not set upon compiling Cyclone DDS
    ValueError
        If endpoint does not have type_id
    RuntimeError
        If type object cannot be retrieved
    """
    if not feature_type_discovery:
        raise DDSException(
            DDSException.DDS_RETCODE_ILLEGAL_OPERATION, 
            "CycloneDDS was not compiled with type support"
        )
    
    if endpoint.type_id is None:
        raise ValueError("Endpoint does not have type_id information")
    
    # Serialize TypeIdentifier (skip first 4 bytes of CDR header)
    type_id_bytes = endpoint.type_id.serialize(use_version_2=True)[4:]
    
    # Call C function to get typeinfo
    result = cl.ddspy_get_endpoint_typeinfo(
        participant._ref,
        type_id_bytes,
        timeout,
        endpoint.topic_name,
        endpoint.type_name
    )
    
    return result


def get_idl_from_endpoint(participant: DomainParticipant, endpoint: DcpsEndpoint, timeout: int) -> str:
    """
    Get IDL string representation from a DCPSPublication or DCPSSubscription endpoint.
    
    This is a convenience function that combines type discovery and IDL generation.
    It retrieves the TypeObject from the endpoint and converts it to IDL using the
    Python IdlType.idl() method.
    
    Parameters
    ----------
    participant: DomainParticipant
        The domain participant to use for type discovery
    endpoint: DcpsEndpoint
        The endpoint (from DCPSPublication or DCPSSubscription builtin topic)
    timeout: int
        Timeout in nanoseconds for type object retrieval
        
    Returns
    -------
    str
        IDL string representation of the type
        
    Raises
    ------
    DDSException
        If ENABLE_TYPE_DISCOVERY is not set upon compiling Cyclone DDS
    ValueError
        If endpoint does not have type_id
    RuntimeError
        If type object cannot be retrieved or IDL generation fails
        
    Examples
    --------
    >>> from cyclonedds import domain, builtin, util
    >>> dp = domain.DomainParticipant()
    >>> reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
    >>> for pub in reader.take(N=10):
    ...     idl = get_idl_from_endpoint(dp, pub, util.duration(seconds=1))
    ...     print(f"Topic: {pub.topic_name}")
    ...     print(idl)
    """
    if not feature_type_discovery:
        raise DDSException(
            DDSException.DDS_RETCODE_ILLEGAL_OPERATION,
            "CycloneDDS was not compiled with type support"
        )
    
    if endpoint.type_id is None:
        raise ValueError("Endpoint does not have type_id information")
    
    # Use existing Python implementation for full type discovery and IDL generation
    from .dynamic import get_types_for_typeid
    
    datatype, all_nested_datatypes = get_types_for_typeid(
        participant, endpoint.type_id, timeout
    )
    
    # Generate IDL string
    idl_string = IdlType.idl([datatype])
    
    return idl_string


def discover_types_from_endpoints(
    participant: DomainParticipant,
    endpoints: list,
    timeout: int
) -> Dict[str, Tuple[str, str]]:
    """
    Discover types from multiple endpoints and return IDL representations.
    
    This function processes multiple endpoints (from DCPSPublication or DCPSSubscription)
    and generates IDL strings for each unique type.
    
    Parameters
    ----------
    participant: DomainParticipant
        The domain participant to use for type discovery
    endpoints: list
        List of DcpsEndpoint objects
    timeout: int
        Timeout in nanoseconds for each type object retrieval
        
    Returns
    -------
    dict
        Dictionary mapping topic_name to (type_name, idl_string) tuples
        
    Examples
    --------
    >>> from cyclonedds import domain, builtin, util
    >>> dp = domain.DomainParticipant()
    >>> pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
    >>> sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)
    >>> endpoints = pub_reader.take(N=100) + sub_reader.take(N=100)
    >>> types = discover_types_from_endpoints(dp, endpoints, util.duration(seconds=2))
    >>> for topic_name, (type_name, idl) in types.items():
    ...     print(f"Topic: {topic_name}, Type: {type_name}")
    ...     print(idl)
    """
    if not feature_type_discovery:
        raise DDSException(
            DDSException.DDS_RETCODE_ILLEGAL_OPERATION,
            "CycloneDDS was not compiled with type support"
        )
    
    discovered_types = {}
    
    for endpoint in endpoints:
        if endpoint.type_id is None:
            continue
            
        topic_name = endpoint.topic_name
        
        # Skip if we've already discovered this topic
        if topic_name in discovered_types:
            continue
        
        try:
            idl_string = get_idl_from_endpoint(participant, endpoint, timeout)
            discovered_types[topic_name] = (endpoint.type_name, idl_string)
        except Exception as e:
            # Log error but continue with other endpoints
            import warnings
            warnings.warn(f"Failed to discover type for topic '{topic_name}': {e}")
    
    return discovered_types


__all__ = [
    'get_endpoint_typeinfo',
    'get_idl_from_endpoint', 
    'discover_types_from_endpoints'
]
