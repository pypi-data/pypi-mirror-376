"""
IB Gateway API Client for K3s Trading Environments

A Python client library for connecting to Interactive Brokers Gateway
running in Kubernetes (K3s) environments for both paper and live trading.
"""

__version__ = "0.1.0"
__author__ = "Logycon"
__email__ = "dev@logycon.com"

from .k3s_paper_client import K3sPaperClient
from .k3s_live_client import K3sLiveClient
from .test_connection import test_connection, get_k3s_node_ip

__all__ = [
    "K3sPaperClient",
    "K3sLiveClient", 
    "test_connection",
    "get_k3s_node_ip",
]
