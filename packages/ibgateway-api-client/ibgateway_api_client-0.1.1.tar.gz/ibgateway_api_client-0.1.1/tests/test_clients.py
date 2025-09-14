"""
Tests for IB Gateway API clients.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from ibgateway_api_client import K3sPaperClient, K3sLiveClient


class TestK3sPaperClient:
    """Test K3sPaperClient functionality."""
    
    def test_init_default(self):
        """Test client initialization with defaults."""
        client = K3sPaperClient()
        assert client.config["connection"]["port"] == 32002
        assert 1000 <= client.config["connection"]["client_id"] <= 9999
    
    def test_init_with_params(self):
        """Test client initialization with parameters."""
        client = K3sPaperClient(host="192.168.1.100", port=4000, client_id=1234)
        assert client.config["connection"]["host"] == "192.168.1.100"
        assert client.config["connection"]["port"] == 4000
        assert client.config["connection"]["client_id"] == 1234
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection."""
        client = K3sPaperClient(host="localhost", port=4000)
        
        with patch.object(client.ib, 'connectAsync') as mock_connect:
            mock_connect.return_value = None
            result = await client.connect()
            assert result is True
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        client = K3sPaperClient(host="localhost", port=4000)
        
        with patch.object(client.ib, 'connectAsync') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            result = await client.connect()
            assert result is False


class TestK3sLiveClient:
    """Test K3sLiveClient functionality."""
    
    def test_init_default(self):
        """Test client initialization with defaults."""
        client = K3sLiveClient()
        assert client.config["connection"]["port"] == 32001
        assert 1000 <= client.config["connection"]["client_id"] <= 9999
    
    def test_init_with_params(self):
        """Test client initialization with parameters."""
        client = K3sLiveClient(host="192.168.1.100", port=4000, client_id=1234)
        assert client.config["connection"]["host"] == "192.168.1.100"
        assert client.config["connection"]["port"] == 4000
        assert client.config["connection"]["client_id"] == 1234


if __name__ == "__main__":
    pytest.main([__file__])
