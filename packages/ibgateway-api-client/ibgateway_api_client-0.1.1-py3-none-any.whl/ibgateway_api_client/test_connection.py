#!/usr/bin/env python3
"""
Connection testing utilities for IB Gateway K3s environments.
"""

import asyncio
import json
import argparse
import subprocess
import sys
import random
from ib_insync import IB

def get_k3s_node_ip():
    """Get the K3s node IP where the pods are running."""
    try:
        # Get all pods with app=ib-gateway
        cmd = [
            'kubectl', 'get', 'pods', '-n', 'ib-gateway', 
            '-l', 'app=ib-gateway', 
            '-o', 'jsonpath={.items[0].metadata.name}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        pod_name = result.stdout.strip()
        
        if not pod_name:
            return "localhost"
        
        # Get the node name for the pod
        cmd = [
            'kubectl', 'get', 'pod', pod_name, '-n', 'ib-gateway',
            '-o', 'jsonpath={.spec.nodeName}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        node_name = result.stdout.strip()
        
        # Get the node IP
        cmd = [
            'kubectl', 'get', 'node', node_name,
            '-o', 'jsonpath={.status.addresses[?(@.type=="InternalIP")].address}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        node_ip = result.stdout.strip().split()[0]  # Get only the first IP (IPv4)
        
        return node_ip if node_ip else "localhost"
        
    except Exception as e:
        print(f"Warning: Could not get K3s node IP: {e}")
        return "localhost"

async def test_connection(host, port, environment, client_id=None):
    """Test connection to IB Gateway."""
    if client_id is None:
        client_id = random.randint(1000, 9999)
    
    ib = IB()
    
    try:
        print(f"Testing {environment} connection to {host}:{port} (client ID: {client_id})...")
        await ib.connectAsync(host, port, clientId=client_id, timeout=5)
        print(f"✅ {environment} connection successful!")
        
        # Get basic account info
        account_summary = await ib.accountSummaryAsync()
        if account_summary:
            print(f"   Found {len(account_summary)} account summary items")
        
        ib.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ {environment} connection failed: {e}")
        return False

async def main():
    """Test environments based on command line arguments."""
    parser = argparse.ArgumentParser(description='Test IB Gateway connections')
    parser.add_argument('--paper', action='store_true', help='Test paper trading only')
    parser.add_argument('--live', action='store_true', help='Test live trading only')
    parser.add_argument('--host', default=None, help='Override host IP')
    args = parser.parse_args()
    
    # Get the K3s node IP
    host = args.host if args.host else get_k3s_node_ip()
    
    print("🔍 Testing K3s IB Gateway Connections")
    print("=" * 40)
    print(f"Host: {host}")
    print()
    
    paper_success = None
    live_success = None
    
    # Test paper trading
    if not args.live:
        paper_success = await test_connection(
            host, 32002, "Paper Trading"
        )
    
    # Test live trading
    if not args.paper:
        live_success = await test_connection(
            host, 32001, "Live Trading"
        )
    
    print("\n📊 Test Results:")
    if paper_success is not None:
        print(f"Paper Trading: {'✅ Success' if paper_success else '❌ Failed'}")
    if live_success is not None:
        print(f"Live Trading:  {'✅ Success' if live_success else '❌ Failed'}")
    
    # Determine overall success
    if args.paper:
        success = paper_success
    elif args.live:
        success = live_success
    else:
        success = (paper_success and live_success) if (paper_success is not None and live_success is not None) else (paper_success or live_success)
    
    if success:
        print("\n🎉 Connection test successful!")
        sys.exit(0)
    else:
        print("\n⚠️  Connection test failed. Check the K3s deployment.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
