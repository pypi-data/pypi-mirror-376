#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-mysql-bailian-licai-202509111610-66e8a1",
    version="2.0.0",
    author="licai-czg",
    author_email="your-email@example.com",
    description="阿里云百炼MCP服务器 - MySQL业务查询服务",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/mcp-mysql-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.1.0",
        "pymysql>=1.0.0",
        "uvicorn>=0.20.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-mysql-bailian-licai-202509111610-66e8a1=mcp_mysql_server.server:main",
        ],
    },
    keywords="mcp mysql bailian alibaba cloud server",
    project_urls={
        "Bug Reports": "https://github.com/your-username/mcp-mysql-server/issues",
        "Source": "https://github.com/your-username/mcp-mysql-server",
    },
)
