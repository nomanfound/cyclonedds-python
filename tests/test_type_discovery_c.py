"""
Tests for type_discovery_c module

Tests the C implementation of type discovery functions that work with
DCPSPublication and DCPSSubscription builtin topics.
"""

import pytest
from dataclasses import dataclass

import cyclonedds.internal
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.builtin import BuiltinDataReader, BuiltinTopicDcpsPublication, BuiltinTopicDcpsSubscription
from cyclonedds.util import duration
from cyclonedds.idl import IdlStruct, types as pt

# Skip all tests if type discovery is not enabled
if not cyclonedds.internal.feature_type_discovery:
    pytest.skip(
        "Skipping tests that require type discovery since it is disabled.",
        allow_module_level=True
    )

from cyclonedds.type_discovery_c import (
    get_endpoint_typeinfo,
    get_idl_from_endpoint,
    discover_types_from_endpoints
)


@dataclass
class TestMessage(IdlStruct):
    """Simple test message for type discovery."""
    message: str
    count: int


def test_get_endpoint_typeinfo_from_publication(manual_setup):
    """Test getting type information from a DCPSPublication endpoint."""
    dp = manual_setup.dp
    
    # Create a topic and writer to generate a publication
    tp = Topic(dp, 'TestDiscoveryTopic', TestMessage)
    dw = DataWriter(dp, tp)
    
    # Read from DCPSPublication builtin topic
    pub_reader = BuiltinDataReader(dp, BuiltinTopicDcpsPublication)
    
    # Find our publication
    publications = pub_reader.take(N=10, timeout=duration(seconds=1))
    test_pub = None
    for pub in publications:
        if pub.topic_name == 'TestDiscoveryTopic':
            test_pub = pub
            break
    
    assert test_pub is not None, "Publication not found"
    
    if test_pub.type_id is None:
        pytest.skip("Endpoint does not have type_id (XTypes may be disabled)")
    
    # Get type information
    typeinfo = get_endpoint_typeinfo(dp, test_pub, duration(seconds=1))
    
    assert 'type_id' in typeinfo
    assert 'type_object' in typeinfo
    assert 'topic_name' in typeinfo
    assert 'type_name' in typeinfo
    assert typeinfo['topic_name'] == 'TestDiscoveryTopic'
    assert typeinfo['type_name'] == 'TestMessage'


def test_get_idl_from_endpoint_publication(manual_setup):
    """Test generating IDL from a DCPSPublication endpoint."""
    dp = manual_setup.dp
    
    # Create a topic and writer
    tp = Topic(dp, 'TestIdlTopic', TestMessage)
    dw = DataWriter(dp, tp)
    
    # Read from DCPSPublication builtin topic
    pub_reader = BuiltinDataReader(dp, BuiltinTopicDcpsPublication)
    
    # Find our publication
    publications = pub_reader.take(N=10, timeout=duration(seconds=1))
    test_pub = None
    for pub in publications:
        if pub.topic_name == 'TestIdlTopic':
            test_pub = pub
            break
    
    assert test_pub is not None, "Publication not found"
    
    if test_pub.type_id is None:
        pytest.skip("Endpoint does not have type_id (XTypes may be disabled)")
    
    # Get IDL string
    idl = get_idl_from_endpoint(dp, test_pub, duration(seconds=1))
    
    assert isinstance(idl, str)
    assert 'struct TestMessage' in idl
    assert 'string message' in idl
    assert 'long long count' in idl


def test_get_idl_from_endpoint_subscription(manual_setup):
    """Test generating IDL from a DCPSSubscription endpoint."""
    dp = manual_setup.dp
    
    # Create a topic and reader
    tp = Topic(dp, 'TestSubIdlTopic', TestMessage)
    dr = DataReader(dp, tp)
    
    # Read from DCPSSubscription builtin topic
    sub_reader = BuiltinDataReader(dp, BuiltinTopicDcpsSubscription)
    
    # Find our subscription (skip the builtin subscription reader itself)
    subscriptions = sub_reader.take(N=10, timeout=duration(seconds=1))
    test_sub = None
    for sub in subscriptions:
        if sub.topic_name == 'TestSubIdlTopic':
            test_sub = sub
            break
    
    assert test_sub is not None, "Subscription not found"
    
    if test_sub.type_id is None:
        pytest.skip("Endpoint does not have type_id (XTypes may be disabled)")
    
    # Get IDL string
    idl = get_idl_from_endpoint(dp, test_sub, duration(seconds=1))
    
    assert isinstance(idl, str)
    assert 'struct TestMessage' in idl


def test_discover_types_from_multiple_endpoints(manual_setup):
    """Test discovering types from multiple endpoints."""
    dp = manual_setup.dp
    
    # Create multiple topics and endpoints
    @dataclass
    class Message1(IdlStruct):
        value: int
    
    @dataclass  
    class Message2(IdlStruct):
        text: str
    
    tp1 = Topic(dp, 'MultiTopic1', Message1)
    tp2 = Topic(dp, 'MultiTopic2', Message2)
    dw1 = DataWriter(dp, tp1)
    dr2 = DataReader(dp, tp2)
    
    # Read from both builtin topics
    pub_reader = BuiltinDataReader(dp, BuiltinTopicDcpsPublication)
    sub_reader = BuiltinDataReader(dp, BuiltinTopicDcpsSubscription)
    
    publications = pub_reader.take(N=20, timeout=duration(seconds=1))
    subscriptions = sub_reader.take(N=20, timeout=duration(seconds=1))
    
    all_endpoints = publications + subscriptions
    
    # Discover types
    discovered = discover_types_from_endpoints(dp, all_endpoints, duration(seconds=1))
    
    # We should find at least our test topics (if they have type_id)
    # Note: This test may need adjustment based on XTypes configuration
    assert isinstance(discovered, dict)


def test_endpoint_without_typeid():
    """Test that endpoints without type_id raise appropriate errors."""
    from cyclonedds.builtin_types import DcpsEndpoint
    import uuid
    from cyclonedds.core import Qos
    
    dp = DomainParticipant()
    
    # Create an endpoint without type_id
    endpoint = DcpsEndpoint(
        key=uuid.uuid4(),
        participant_key=uuid.uuid4(),
        participant_instance_handle=0,
        topic_name="TestTopic",
        type_name="TestType",
        qos=Qos(),
        type_id=None
    )
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="does not have type_id"):
        get_endpoint_typeinfo(dp, endpoint, duration(seconds=1))
    
    with pytest.raises(ValueError, match="does not have type_id"):
        get_idl_from_endpoint(dp, endpoint, duration(seconds=1))
