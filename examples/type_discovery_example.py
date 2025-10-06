#!/usr/bin/env python3
"""
Example script demonstrating the use of type discovery C functions.

This script shows how to use DCPSPublication and DCPSSubscription builtin topics
to discover types on the network and generate IDL representations.

Usage:
    python examples/type_discovery_example.py
"""

import time
from cyclonedds import domain, builtin, util
from cyclonedds.type_discovery_c import get_idl_from_endpoint, discover_types_from_endpoints


def main():
    """
    Main function demonstrating type discovery from endpoints.
    """
    print("Type Discovery Example")
    print("=" * 60)
    print()
    
    # Create domain participant
    dp = domain.DomainParticipant()
    
    # Create readers for DCPSPublication and DCPSSubscription builtin topics
    pub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsPublication)
    sub_reader = builtin.BuiltinDataReader(dp, builtin.BuiltinTopicDcpsSubscription)
    
    print("Waiting for endpoints to be discovered...")
    print("(You may need to run other DDS applications to see results)")
    print()
    
    # Wait a bit for discovery
    time.sleep(2)
    
    # Read publications
    publications = pub_reader.take(N=100)
    print(f"Found {len(publications)} publications")
    
    # Read subscriptions
    subscriptions = sub_reader.take(N=100)
    print(f"Found {len(subscriptions)} subscriptions")
    print()
    
    # Combine all endpoints
    all_endpoints = publications + subscriptions
    
    if not all_endpoints:
        print("No endpoints discovered. Make sure other DDS applications are running.")
        return
    
    # Discover types from all endpoints
    print("Discovering types from endpoints...")
    print()
    
    try:
        discovered_types = discover_types_from_endpoints(
            dp, 
            all_endpoints, 
            util.duration(seconds=2)
        )
        
        if discovered_types:
            print(f"Successfully discovered {len(discovered_types)} unique types:")
            print()
            
            for topic_name, (type_name, idl) in discovered_types.items():
                print("-" * 60)
                print(f"Topic: {topic_name}")
                print(f"Type: {type_name}")
                print()
                print("IDL Definition:")
                print(idl)
                print()
        else:
            print("No types could be discovered (endpoints may not have type_id)")
            
    except Exception as e:
        print(f"Error during type discovery: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("Example: Discover individual endpoint")
    print("-" * 60)
    
    # Try to discover from first endpoint with type_id
    for endpoint in all_endpoints:
        if endpoint.type_id is not None:
            print(f"Topic: {endpoint.topic_name}")
            print(f"Type: {endpoint.type_name}")
            try:
                idl = get_idl_from_endpoint(dp, endpoint, util.duration(seconds=2))
                print()
                print("IDL Definition:")
                print(idl)
            except Exception as e:
                print(f"Error: {e}")
            break
    else:
        print("No endpoints with type_id found")


if __name__ == "__main__":
    main()
