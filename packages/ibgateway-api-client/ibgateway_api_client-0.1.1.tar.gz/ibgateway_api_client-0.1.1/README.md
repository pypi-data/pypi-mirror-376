# IB Gateway API Client

A Python client library for connecting to Interactive Brokers Gateway running in Kubernetes (K3s) environments for both paper and live trading.

## Features

- 🚀 **Easy Integration**: Simple Python API for connecting to IB Gateway
- 🔄 **Async Support**: Built on `ib-insync` with full async/await support
- 🏗️ **K3s Ready**: Automatically detects K3s node IPs and service endpoints
- 📊 **Account Management**: Get account information, positions, and trading data
- 🔒 **Secure**: Random client ID generation to prevent connection conflicts
- 📦 **PyPI Ready**: Installable via pip from PyPI

## Installation

```bash
pip install ibgateway-api-client
```

## Quick Start

### Paper Trading

```python
import asyncio
from ibgateway_api_client import K3sPaperClient

async def main():
    client = K3sPaperClient(host="192.168.1.222", port=32002)
    
    if await client.connect():
        await client.get_account_info()
        await client.get_positions()
        await client.disconnect()

asyncio.run(main())
```

### Live Trading

```python
import asyncio
from ibgateway_api_client import K3sLiveClient

async def main():
    client = K3sLiveClient(host="192.168.1.222", port=32001)
    
    if await client.connect():
        await client.get_account_info()
        await client.get_positions()
        await client.disconnect()

asyncio.run(main())
```

### Auto-Detection (K3s)

```python
import asyncio
from ibgateway_api_client import K3sPaperClient, get_k3s_node_ip

async def main():
    # Automatically detect K3s node IP
    host = get_k3s_node_ip()
    client = K3sPaperClient(host=host, port=32002)
    
    if await client.connect():
        await client.get_account_info()
        await client.disconnect()

asyncio.run(main())
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Paper Trading
K3S_PAPER_HOST=192.168.1.222
K3S_PAPER_PORT=32002
K3S_PAPER_CLIENT_ID=1001

# Live Trading
K3S_LIVE_HOST=192.168.1.222
K3S_LIVE_PORT=32001
K3S_LIVE_CLIENT_ID=1002
```

### Configuration File

```python
# config.json
{
    "connection": {
        "host": "192.168.1.222",
        "port": 32002,
        "client_id": 1001,
        "timeout": 10
    }
}

# Usage
client = K3sPaperClient(config_file="config.json")
```

## API Reference

### K3sPaperClient

Paper trading client for K3s environments.

```python
client = K3sPaperClient(host=None, port=32002, client_id=None, config_file=None)
```

**Parameters:**
- `host` (str, optional): Gateway host IP. Defaults to auto-detection.
- `port` (int, optional): Gateway port. Defaults to 32002 for paper trading.
- `client_id` (int, optional): Client ID. Defaults to random (1000-9999).
- `config_file` (str, optional): Path to JSON configuration file.

**Methods:**
- `async connect()`: Connect to the gateway
- `async get_account_info()`: Get account summary information
- `async get_positions()`: Get current positions
- `async disconnect()`: Disconnect from the gateway

### K3sLiveClient

Live trading client for K3s environments.

```python
client = K3sLiveClient(host=None, port=32001, client_id=None, config_file=None)
```

**Parameters:**
- `host` (str, optional): Gateway host IP. Defaults to auto-detection.
- `port` (int, optional): Gateway port. Defaults to 32001 for live trading.
- `client_id` (int, optional): Client ID. Defaults to random (1000-9999).
- `config_file` (str, optional): Path to JSON configuration file.

**Methods:**
- `async connect()`: Connect to the gateway
- `async get_account_info()`: Get account summary information
- `async get_positions()`: Get current positions
- `async disconnect()`: Disconnect from the gateway

### Utility Functions

```python
from ibgateway_api_client import get_k3s_node_ip, test_connection

# Get K3s node IP automatically
host = get_k3s_node_ip()

# Test connection
success = await test_connection(host, 32002, "Paper Trading")
```

## Command Line Tools

The package includes command-line tools for testing connections:

```bash
# Test paper trading connection
ibgateway-test-paper

# Test live trading connection
ibgateway-test-live

# Test both connections
python -m ibgateway_api_client.test_connection
```

## Requirements

- Python 3.8+
- Interactive Brokers Gateway running in K3s
- `ib-insync` library
- `kubectl` configured for K3s cluster access

## Development

### Setup

```bash
git clone https://github.com/logycon/ibgateway-api-client
cd ibgateway-api-client
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Building

```bash
python -m build
```

### Publishing

```bash
python -m twine upload dist/*
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

- 📖 [Documentation](https://github.com/logycon/ibgateway-api-client#readme)
- 🐛 [Issue Tracker](https://github.com/logycon/ibgateway-api-client/issues)
- 💬 [Discussions](https://github.com/logycon/ibgateway-api-client/discussions)

## Disclaimer

This library is for educational and development purposes. Always test thoroughly in paper trading before using with live accounts. The authors are not responsible for any financial losses.
