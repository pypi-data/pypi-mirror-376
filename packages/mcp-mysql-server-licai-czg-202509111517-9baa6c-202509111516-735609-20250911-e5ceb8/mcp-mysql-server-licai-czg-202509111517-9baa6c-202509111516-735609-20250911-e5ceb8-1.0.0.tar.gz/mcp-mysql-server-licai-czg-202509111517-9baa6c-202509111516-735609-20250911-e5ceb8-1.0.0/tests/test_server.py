#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic tests for MCP MySQL Server
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import our module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_mysql_server.server import MySQLManager, MYSQL_CONFIG


class TestMySQLManager:
    """Test cases for MySQLManager class"""
    
    def test_mysql_config_defaults(self):
        """Test that MySQL config has expected default values"""
        assert MYSQL_CONFIG['host'] == 'localhost'
        assert MYSQL_CONFIG['port'] == 3306
        assert MYSQL_CONFIG['user'] == 'root'
        assert MYSQL_CONFIG['charset'] == 'utf8mb4'
    
    @patch.dict(os.environ, {
        'MYSQL_HOST': 'test-host',
        'MYSQL_PORT': '3307',
        'MYSQL_USER': 'test-user',
        'MYSQL_PASSWORD': 'test-pass',
        'MYSQL_DATABASES': 'db1,db2'
    })
    def test_mysql_config_from_env(self):
        """Test that MySQL config reads from environment variables"""
        # Reload the module to pick up new env vars
        import importlib
        from mcp_mysql_server import server
        importlib.reload(server)
        
        config = server.MYSQL_CONFIG
        assert config['host'] == 'test-host'
        assert config['port'] == 3307
        assert config['user'] == 'test-user'
        assert config['password'] == 'test-pass'
    
    def test_mysql_manager_init(self):
        """Test MySQLManager initialization"""
        manager = MySQLManager()
        assert manager is not None
        assert hasattr(manager, 'test_connection')
    
    @pytest.mark.asyncio
    async def test_mysql_manager_connection_failure(self):
        """Test MySQL connection failure handling"""
        manager = MySQLManager()
        
        # Mock pymysql.connect to raise an exception
        with patch('pymysql.connect', side_effect=Exception("Connection failed")):
            result = await manager.test_connection()
            assert result is False


class TestServerFunctions:
    """Test cases for server functions"""
    
    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            from mcp_mysql_server.server import main, MySQLManager
            assert callable(main)
            assert MySQLManager is not None
        except ImportError as e:
            pytest.fail(f"Failed to import required modules: {e}")
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable"""
        from mcp_mysql_server.server import main
        assert callable(main)


if __name__ == "__main__":
    pytest.main([__file__])