#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="mcp-mysql-server-licai-czg-202509111517-9baa6c-202509111516-735609-20250911-e5ceb8",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A MySQL MCP Server for cross-database queries with Chinese field mapping",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mcp-mysql-server",
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
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "mcp-mysql-server-licai-czg-202509111517-9baa6c-202509111516-735609=mcp_mysql_server.server:main",
        ],
    },
    keywords="mcp mysql server database cross-database chinese",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/mcp-mysql-server/issues",
        "Source": "https://github.com/yourusername/mcp-mysql-server",
        "Documentation": "https://github.com/yourusername/mcp-mysql-server#readme",
    },
    include_package_data=True,
    zip_safe=False,
)