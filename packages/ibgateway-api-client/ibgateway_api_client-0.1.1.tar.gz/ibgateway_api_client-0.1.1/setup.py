#!/usr/bin/env python3
"""
Setup script for ibgateway-api-client package.
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ibgateway-api-client",
    version="0.1.1",
    author="Logycon",
    author_email="dev@logycon.com",
    description="Python client library for Interactive Brokers Gateway running in Kubernetes (K3s) environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/logycon/ibgateway-api-client",
    project_urls={
        "Bug Tracker": "https://github.com/logycon/ibgateway-api-client/issues",
        "Documentation": "https://github.com/logycon/ibgateway-api-client#readme",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "ib-insync>=0.9.86",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ibgateway-test-paper=ibgateway_api_client.test_connection:main",
            "ibgateway-test-live=ibgateway_api_client.test_connection:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
