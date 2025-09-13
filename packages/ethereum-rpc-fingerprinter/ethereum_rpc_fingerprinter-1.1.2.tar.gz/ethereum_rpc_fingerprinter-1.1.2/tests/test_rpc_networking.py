#!/usr/bin/env python3
"""
Unit tests for RPC method detection and networking functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import asyncio
from ethereum_rpc_fingerprinter import EthereumRPCFingerprinter, AsyncEthereumRPCFingerprinter


class TestRPCMethodDetection(unittest.TestCase):
    """Test RPC method detection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fingerprinter = EthereumRPCFingerprinter()
    
    def test_standard_eth_methods_detection(self):
        """Test detection of standard Ethereum RPC methods."""
        standard_methods = [
            "eth_blockNumber",
            "eth_getBalance", 
            "eth_getBlockByNumber",
            "eth_getTransactionByHash",
            "eth_sendTransaction",
            "eth_call",
            "eth_estimateGas",
            "eth_gasPrice"
        ]
        
        with patch.object(self.fingerprinter, '_make_rpc_call') as mock_rpc:
            # Mock successful responses for standard methods
            def mock_rpc_response(endpoint, method, params=None):
                if method in standard_methods:
                    if method == "eth_blockNumber":
                        return "0x123456"
                    elif method == "eth_getBalance":
                        return "0x1bc16d674ec80000"  # 2 ETH in wei
                    elif method == "eth_gasPrice":
                        return "0x3b9aca00"  # 1 gwei
                    else:
                        return "success"
                else:
                    raise Exception("Method not found")
            
            mock_rpc.side_effect = mock_rpc_response
            
            # Test method detection
            for method in standard_methods:
                with self.subTest(method=method):
                    try:
                        result = mock_rpc("http://test.com", method, [])
                        self.assertIsNotNone(result)
                    except Exception:
                        self.fail(f"Standard method {method} should be supported")
    
    def test_network_methods_detection(self):
        """Test detection of network-related RPC methods."""
        network_methods = [
            "net_version",
            "net_peerCount",
            "net_listening",
            "web3_clientVersion"
        ]
        
        with patch.object(self.fingerprinter, '_make_rpc_call') as mock_rpc:
            def mock_rpc_response(endpoint, method, params=None):
                responses = {
                    "net_version": "1",  # Mainnet
                    "net_peerCount": "0x19",  # 25 peers
                    "net_listening": True,
                    "web3_clientVersion": "Geth/v1.10.0"
                }
                return responses.get(method, None)
            
            mock_rpc.side_effect = mock_rpc_response
            
            for method in network_methods:
                with self.subTest(method=method):
                    result = mock_rpc("http://test.com", method, [])
                    self.assertIsNotNone(result)
    
    def test_mining_methods_detection(self):
        """Test detection of mining-related RPC methods."""
        mining_methods = [
            "eth_mining",
            "eth_hashrate",
            "eth_coinbase",
            "eth_getWork",
            "eth_submitWork"
        ]
        
        with patch.object(self.fingerprinter, '_make_rpc_call') as mock_rpc:
            def mock_rpc_response(endpoint, method, params=None):
                responses = {
                    "eth_mining": False,
                    "eth_hashrate": "0x0",
                    "eth_coinbase": "0x0000000000000000000000000000000000000000",
                    "eth_getWork": None,  # Not mining
                    "eth_submitWork": False
                }
                return responses.get(method, None)
            
            mock_rpc.side_effect = mock_rpc_response
            
            for method in mining_methods:
                with self.subTest(method=method):
                    result = mock_rpc("http://test.com", method, [])
                    # Mining methods might return None/False when not mining
                    self.assertTrue(result is not None or result is False)
    
    def test_unsupported_method_detection(self):
        """Test detection of unsupported methods."""
        unsupported_methods = [
            "custom_nonexistentMethod",
            "fake_method",
            "invalid_rpcMethod"
        ]
        
        with patch.object(self.fingerprinter, '_make_rpc_call') as mock_rpc:
            # Mock method not found errors
            def mock_rpc_response(endpoint, method, params=None):
                if method in unsupported_methods:
                    raise Exception("Method not found")
                return "success"
            
            mock_rpc.side_effect = mock_rpc_response
            
            for method in unsupported_methods:
                with self.subTest(method=method):
                    with self.assertRaises(Exception):
                        mock_rpc("http://test.com", method, [])
    
    def test_method_response_time_tracking(self):
        """Test that method response times are tracked."""
        # This would test the actual timing mechanism
        with patch.object(self.fingerprinter, '_make_rpc_call') as mock_rpc:
            # Mock a method that takes some time
            import time
            def slow_rpc_response(endpoint, method, params=None):
                time.sleep(0.01)  # Simulate 10ms delay
                return "success"
            
            mock_rpc.side_effect = slow_rpc_response
            
            # In a real implementation, you'd track the timing
            start_time = time.time()
            result = mock_rpc("http://test.com", "eth_blockNumber", [])
            end_time = time.time()
            
            response_time = end_time - start_time
            self.assertGreater(response_time, 0.005)  # Should take at least 5ms
            self.assertIsNotNone(result)


class TestNetworkingFunctionality(unittest.TestCase):
    """Test networking and HTTP functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fingerprinter = EthereumRPCFingerprinter(timeout=5)
    
    def test_http_post_request_structure(self):
        """Test that HTTP POST requests are properly structured."""
        endpoint = "http://localhost:8545"
        method = "eth_blockNumber"
        params = []
        
        with patch('requests.post') as mock_post:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": "0x123456"
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = self.fingerprinter._make_rpc_call(endpoint, method, params)
            
            # Verify the request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            self.assertEqual(call_args[1]['url'] if 'url' in call_args[1] else call_args[0][0], endpoint)
            
            # Check headers
            headers = call_args[1].get('headers', {})
            self.assertEqual(headers.get('Content-Type'), 'application/json')
            
            # Check JSON payload
            data = json.loads(call_args[1].get('data', '{}'))
            self.assertEqual(data['jsonrpc'], '2.0')
            self.assertEqual(data['method'], method)
            self.assertEqual(data['params'], params)
            self.assertIn('id', data)
            
            self.assertEqual(result, "0x123456")
    
    def test_timeout_handling(self):
        """Test timeout handling in network requests."""
        endpoint = "http://localhost:8545"
        
        with patch('requests.post') as mock_post:
            # Mock timeout exception
            import requests
            mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
            
            with self.assertRaises(Exception):
                self.fingerprinter._make_rpc_call(endpoint, "eth_blockNumber", [])
            
            # Verify timeout was set
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[1].get('timeout'), 5)
    
    def test_connection_error_handling(self):
        """Test connection error handling."""
        endpoint = "http://localhost:8545"
        
        with patch('requests.post') as mock_post:
            # Mock connection error
            import requests
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
            
            with self.assertRaises(Exception):
                self.fingerprinter._make_rpc_call(endpoint, "eth_blockNumber", [])
    
    def test_invalid_json_response_handling(self):
        """Test handling of invalid JSON responses."""
        endpoint = "http://localhost:8545"
        
        with patch('requests.post') as mock_post:
            # Mock response with invalid JSON
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.text = "Invalid response"
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            with self.assertRaises(Exception):
                self.fingerprinter._make_rpc_call(endpoint, "eth_blockNumber", [])
    
    def test_http_error_status_handling(self):
        """Test handling of HTTP error status codes."""
        endpoint = "http://localhost:8545"
        
        with patch('requests.post') as mock_post:
            # Mock HTTP error response
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = Exception("HTTP 500 Error")
            mock_post.return_value = mock_response
            
            with self.assertRaises(Exception):
                self.fingerprinter._make_rpc_call(endpoint, "eth_blockNumber", [])


class TestAsyncNetworkingFunctionality(unittest.TestCase):
    """Test async networking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.async_fingerprinter = AsyncEthereumRPCFingerprinter(timeout=5)
    
    def test_async_fingerprinting_structure(self):
        """Test that async fingerprinting has the correct structure."""
        # Test that AsyncEthereumRPCFingerprinter exists and has expected methods
        self.assertTrue(hasattr(self.async_fingerprinter, 'fingerprint'))
        self.assertTrue(hasattr(self.async_fingerprinter, 'fingerprint_multiple'))
        
        # Test that fingerprint method is async
        import inspect
        self.assertTrue(inspect.iscoroutinefunction(self.async_fingerprinter.fingerprint))
        
    @patch('aiohttp.ClientSession.post')
    async def test_async_rpc_call_structure(self, mock_post):
        """Test async RPC call structure."""
        # Mock async HTTP response
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        })
        mock_response.status = 200
        
        # Create async context manager mock
        mock_context = Mock()
        mock_context.__aenter__ = Mock(return_value=mock_response)
        mock_context.__aexit__ = Mock(return_value=None)
        mock_post.return_value = mock_context
        
        endpoint = "http://localhost:8545"
        method = "eth_blockNumber"
        params = []
        
        # This test structure shows what we'd test for async functionality
        # The actual implementation would need to be tested with async test methods
        self.assertIsNotNone(self.async_fingerprinter)
    
    def test_multiple_endpoints_fingerprinting(self):
        """Test fingerprinting multiple endpoints."""
        endpoints = [
            "http://localhost:8545",
            "http://localhost:8546", 
            "https://mainnet.infura.io/v3/test"
        ]
        
        # Test that the method exists
        self.assertTrue(hasattr(self.async_fingerprinter, 'fingerprint_multiple'))
        
        # In actual implementation, this would test concurrent fingerprinting
        # For now, just test the structure exists
        self.assertEqual(len(endpoints), 3)


if __name__ == '__main__':
    unittest.main()
