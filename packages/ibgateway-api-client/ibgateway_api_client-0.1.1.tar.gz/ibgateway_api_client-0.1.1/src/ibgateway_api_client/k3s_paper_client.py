#!/usr/bin/env python3
"""
Sample client for connecting to IB Gateway paper trading on K3s.
This demonstrates how to connect to the paper trading environment.
"""

import asyncio
import json
import random
from ib_insync import IB, util

class K3sPaperClient:
    def __init__(self, config_file=None, host=None, port=32002, client_id=None):
        """Initialize the client with configuration."""
        if config_file:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                "connection": {
                    "host": host or "192.168.1.222",
                    "port": port,
                    "client_id": client_id or random.randint(1000, 9999),
                    "timeout": 10
                }
            }
        
        self.ib = IB()
    
    async def connect(self):
        """Connect to the paper trading gateway."""
        try:
            conn = self.config["connection"]
            print(f"Connecting to paper trading on {conn['host']}:{conn['port']}...")
            
            await self.ib.connectAsync(
                conn["host"], 
                conn["port"], 
                clientId=conn["client_id"],
                timeout=conn["timeout"]
            )
            
            print("✅ Connected to paper trading successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("Make sure API port on TWS/IBG is open")
            return False
    
    async def get_account_info(self):
        """Get account information."""
        try:
            print("\n📊 Paper Trading Account Information")
            print("=" * 40)
            
            # Get account summary
            account_summary = await self.ib.accountSummaryAsync()
            
            if not account_summary:
                print("No account summary available")
                return
            
            # Group by account
            accounts = {}
            for item in account_summary:
                account = item.account
                if account not in accounts:
                    accounts[account] = {}
                accounts[account][item.tag] = item.value
            
            for account, data in accounts.items():
                print(f"\nAccount: {account}")
                print("-" * 20)
                
                # Display key information
                key_fields = [
                    'TotalCashValue', 'NetLiquidation', 'BuyingPower',
                    'AvailableFunds', 'ExcessLiquidity', 'DayTradesRemaining'
                ]
                
                for field in key_fields:
                    if field in data:
                        value = data[field]
                        if field in ['TotalCashValue', 'NetLiquidation', 'BuyingPower', 
                                   'AvailableFunds', 'ExcessLiquidity']:
                            try:
                                value = f"${float(value):,.2f}"
                            except (ValueError, TypeError):
                                pass
                        print(f"  {field}: {value}")
            
        except Exception as e:
            print(f"Error getting account info: {e}")
    
    async def get_positions(self):
        """Get current positions."""
        try:
            print("\n📈 Current Positions")
            print("=" * 20)
            
            positions = self.ib.positions()
            
            if not positions:
                print("No positions found")
            else:
                print(f"{'Symbol':<15} {'Position':<10} {'Market Price':<15} {'Market Value':<15}")
                print("-" * 60)
                for pos in positions:
                    symbol = pos.contract.symbol if pos.contract else 'Unknown'
                    position = pos.position
                    market_price = f"${pos.marketPrice:.2f}" if pos.marketPrice else "N/A"
                    market_value = f"${pos.marketValue:.2f}" if pos.marketValue else "N/A"
                    print(f"{symbol:<15} {position:<10} {market_price:<15} {market_value:<15}")
            
        except Exception as e:
            print(f"Error getting positions: {e}")
    
    async def disconnect(self):
        """Disconnect from the gateway."""
        try:
            if self.ib.isConnected():
                self.ib.disconnect()
                print("\n✅ Disconnected from paper trading")
        except Exception as e:
            print(f"Error disconnecting: {e}")

async def main():
    """Main function."""
    client = K3sPaperClient()
    
    try:
        # Connect
        if not await client.connect():
            return
        
        # Get account information
        await client.get_account_info()
        
        # Get positions
        await client.get_positions()
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Always disconnect
        await client.disconnect()

if __name__ == "__main__":
    # Use a different approach to handle event loop issues
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print(f"\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
