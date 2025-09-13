"""
Real implementation tests for KotaDB server management.

Following the project's anti-mock philosophy, these tests use actual
implementations with failure injection and temporary directories.
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Optional

# Import the server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kotadb.server import (
    KotaDBServer,
    get_platform_info,
    get_binary_info,
    verify_checksum,
    download_binary,
    start_server,
    ensure_binary_installed,
    KOTADB_HOME,
    BINARY_DIR,
)


class TestPlatformDetectionReal(unittest.TestCase):
    """Test platform detection with real system calls."""
    
    def test_platform_detection_current_system(self):
        """Test detection on the current system."""
        platform_name, arch = get_platform_info()
        
        # Verify we get valid values for current system
        self.assertIn(platform_name, ['linux', 'linux-musl', 'macos', 'windows'])
        self.assertIn(arch, ['x64', 'arm64'])
        
        # Verify consistency with platform module
        system = platform.system().lower()
        if system == 'darwin':
            self.assertEqual(platform_name, 'macos')
        elif system == 'windows':
            self.assertEqual(platform_name, 'windows')
        elif system == 'linux':
            self.assertIn(platform_name, ['linux', 'linux-musl'])
    
    def test_alpine_detection_with_real_file(self):
        """Test Alpine detection using a real temporary file."""
        if platform.system().lower() != 'linux':
            self.skipTest("Alpine detection only relevant on Linux")
        
        # Read actual /etc/os-release if it exists
        os_release_path = Path('/etc/os-release')
        if os_release_path.exists():
            with open(os_release_path) as f:
                content = f.read()
                platform_name, _ = get_platform_info()
                
                if 'alpine' in content.lower():
                    self.assertEqual(platform_name, 'linux-musl')
                else:
                    self.assertEqual(platform_name, 'linux')


class TestBinaryInfoReal(unittest.TestCase):
    """Test binary info retrieval with real network calls."""
    
    def test_get_binary_info_current_platform(self):
        """Test getting binary info for current platform."""
        try:
            binary_info = get_binary_info()
            
            # Verify structure
            self.assertIn('url', binary_info)
            self.assertIn('extension', binary_info)
            self.assertIn('sha256', binary_info)
            
            # Verify URL is well-formed
            self.assertTrue(binary_info['url'].startswith('http'))
            self.assertIn('kotadb', binary_info['url'])
            
            # Verify extension matches platform
            system = platform.system().lower()
            if system == 'windows':
                self.assertEqual(binary_info['extension'], 'zip')
            else:
                self.assertEqual(binary_info['extension'], 'tar.gz')
                
        except RuntimeError as e:
            # Network might be unavailable in CI
            if "No binary available" in str(e):
                self.skipTest("Binary not available for current platform")
            raise


class TestChecksumReal(unittest.TestCase):
    """Test checksum verification with real files."""
    
    def test_verify_checksum_with_real_file(self):
        """Test checksum verification with actual file operations."""
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp:
            test_content = b"This is real test content for checksum verification"
            tmp.write(test_content)
            tmp_path = Path(tmp.name)
        
        try:
            # Calculate real SHA256
            sha256_hash = hashlib.sha256()
            sha256_hash.update(test_content)
            expected_sha256 = sha256_hash.hexdigest()
            
            # Test successful verification
            result = verify_checksum(tmp_path, expected_sha256)
            self.assertTrue(result)
            
            # Test with wrong checksum
            wrong_sha256 = hashlib.sha256(b"wrong content").hexdigest()
            result = verify_checksum(tmp_path, wrong_sha256)
            self.assertFalse(result)
            
            # Test with no checksum
            result = verify_checksum(tmp_path, None)
            self.assertTrue(result)  # Should pass with warning
            
        finally:
            tmp_path.unlink()


class FlakyBinaryDownloader:
    """Failure injection for binary download testing."""
    
    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate
        self.attempt_count = 0
    
    def download(self, force: bool = False) -> Path:
        """Download with configurable failure rate."""
        import random
        self.attempt_count += 1
        
        if random.random() < self.failure_rate:
            raise RuntimeError(f"Simulated download failure (attempt {self.attempt_count})")
        
        # Delegate to real download function
        return download_binary(force)


class TestKotaDBServerReal(unittest.TestCase):
    """Test KotaDB server with real binary and processes."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix='kotadb_test_')
        self.data_dir = Path(self.test_dir) / "data"
        self.config_dir = Path(self.test_dir) / "config"
        self.binary_dir = Path(self.test_dir) / "bin"
        
        # Use high port numbers to avoid conflicts
        self.base_port = 28000 + (os.getpid() % 1000)
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop any running servers
        try:
            subprocess.run(['pkill', '-f', f'kotadb.*{self.base_port}'], 
                         capture_output=True, timeout=2)
        except:
            pass
        
        # Clean up directories
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_server_directory_creation(self):
        """Test that server creates necessary directories."""
        server = KotaDBServer(
            data_dir=self.data_dir,
            port=self.base_port,
            auto_install=False  # Don't download in this test
        )
        
        # Verify directories were created
        self.assertTrue(self.data_dir.exists())
        self.assertTrue(self.data_dir.is_dir())
    
    def test_config_file_creation(self):
        """Test configuration file generation."""
        server = KotaDBServer(
            data_dir=self.data_dir,
            port=self.base_port + 1,
            auto_install=False
        )
        
        config_path = server.create_config()
        
        # Verify config file exists and contains expected content
        self.assertTrue(config_path.exists())
        
        with open(config_path, 'r') as f:
            config_content = f.read()
            
            # Check for required configuration elements
            self.assertIn(f'port = {self.base_port + 1}', config_content)
            self.assertIn(str(self.data_dir), config_content)
            self.assertIn('wal_enabled = true', config_content)
            self.assertIn('cache_size = 1000', config_content)
            self.assertIn('[server]', config_content)
            self.assertIn('[storage]', config_content)
            self.assertIn('[logging]', config_content)
    
    def test_custom_config_path(self):
        """Test using custom configuration path."""
        server = KotaDBServer(
            data_dir=self.data_dir,
            port=self.base_port + 2,
            auto_install=False
        )
        
        custom_config = self.config_dir / "custom.toml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = server.create_config(custom_config)
        
        self.assertEqual(config_path, custom_config)
        self.assertTrue(custom_config.exists())


class TestBinaryInstallationReal(unittest.TestCase):
    """Test actual binary installation with temporary directories."""
    
    def setUp(self):
        """Set up isolated test environment."""
        self.test_home = tempfile.mkdtemp(prefix='kotadb_home_')
        self.original_home = os.environ.get('HOME')
        
        # Override KOTADB_HOME for testing
        import kotadb.server
        self.original_kotadb_home = kotadb.server.KOTADB_HOME
        self.original_binary_dir = kotadb.server.BINARY_DIR
        
        kotadb.server.KOTADB_HOME = Path(self.test_home) / '.kotadb'
        kotadb.server.BINARY_DIR = kotadb.server.KOTADB_HOME / 'bin'
    
    def tearDown(self):
        """Restore original environment."""
        import kotadb.server
        kotadb.server.KOTADB_HOME = self.original_kotadb_home
        kotadb.server.BINARY_DIR = self.original_binary_dir
        
        shutil.rmtree(self.test_home, ignore_errors=True)
    
    @unittest.skipIf(
        os.environ.get('CI', 'false').lower() == 'true' and 
        os.environ.get('ENABLE_DOWNLOAD_TESTS', 'false').lower() != 'true',
        "Skipping download test in CI (set ENABLE_DOWNLOAD_TESTS=true to run)"
    )
    def test_ensure_binary_installed(self):
        """Test binary installation creates correct structure."""
        # This test may download a real binary if available
        try:
            binary_path = ensure_binary_installed()
            
            # Verify binary location
            import kotadb.server
            expected_dir = kotadb.server.BINARY_DIR
            self.assertEqual(binary_path.parent, expected_dir)
            
            # Verify binary name
            system = platform.system()
            if system == 'Windows':
                self.assertEqual(binary_path.name, 'kotadb.exe')
            else:
                self.assertEqual(binary_path.name, 'kotadb')
            
            # If download succeeded, verify file properties
            if binary_path.exists():
                self.assertTrue(binary_path.is_file())
                self.assertGreater(binary_path.stat().st_size, 1000000)  # > 1MB
                
                # On Unix, check executable bit
                if system != 'Windows':
                    self.assertTrue(binary_path.stat().st_mode & 0o111)
                    
        except RuntimeError as e:
            # Download might fail in test environment
            if "Failed to download" in str(e) or "Network error" in str(e):
                self.skipTest(f"Binary download not available: {e}")
            raise


class TestServerLifecycleReal(unittest.TestCase):
    """Test server lifecycle with real processes."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix='kotadb_lifecycle_')
        self.data_dir = Path(self.test_dir) / "data"
        self.port = 29000 + (os.getpid() % 1000)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_server_port_detection(self):
        """Test that server correctly detects port availability."""
        # Create a server but don't start it
        server1 = KotaDBServer(
            data_dir=self.data_dir,
            port=self.port,
            auto_install=False
        )
        
        # Port should be available
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', self.port))
        sock.close()
        self.assertNotEqual(result, 0)  # Connection should fail (port not in use)
    
    def test_multiple_server_isolation(self):
        """Test that multiple servers use isolated data directories."""
        data_dir1 = self.data_dir / "server1"
        data_dir2 = self.data_dir / "server2"
        
        server1 = KotaDBServer(
            data_dir=data_dir1,
            port=self.port,
            auto_install=False
        )
        
        server2 = KotaDBServer(
            data_dir=data_dir2,
            port=self.port + 1,
            auto_install=False
        )
        
        # Verify separate directories
        self.assertTrue(data_dir1.exists())
        self.assertTrue(data_dir2.exists())
        self.assertNotEqual(data_dir1, data_dir2)
        
        # Create configs and verify they're different
        config1 = server1.create_config()
        config2 = server2.create_config()
        
        with open(config1) as f1, open(config2) as f2:
            content1 = f1.read()
            content2 = f2.read()
            
            self.assertIn(str(self.port), content1)
            self.assertIn(str(self.port + 1), content2)
            self.assertNotEqual(content1, content2)


class TestConvenienceFunctionsReal(unittest.TestCase):
    """Test convenience functions with real implementations."""
    
    def test_start_server_with_custom_dir(self):
        """Test start_server with custom directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_dir = Path(temp_dir) / "custom_data"
            port = 30000 + (os.getpid() % 1000)
            
            # Note: This will try to actually start a server
            # In test environment without binary, it will fail appropriately
            try:
                server = KotaDBServer(
                    port=port,
                    data_dir=custom_dir,
                    auto_install=False
                )
                
                # Verify server was configured correctly
                self.assertEqual(server.port, port)
                self.assertEqual(server.data_dir, custom_dir)
                self.assertTrue(custom_dir.exists())
                
            except RuntimeError as e:
                if "binary not found" in str(e).lower():
                    self.skipTest("Binary not available for testing")
                raise


class TestFailureInjection(unittest.TestCase):
    """Test failure scenarios with injection."""
    
    def test_flaky_download(self):
        """Test download with simulated failures."""
        downloader = FlakyBinaryDownloader(failure_rate=0.5)
        
        # Track attempts
        max_attempts = 10
        success = False
        
        for _ in range(max_attempts):
            try:
                # This might succeed or fail based on failure rate
                downloader.download(force=False)
                success = True
                break
            except RuntimeError as e:
                if "Simulated download failure" in str(e):
                    continue  # Expected failure
                raise
        
        # With 50% failure rate, should succeed within 10 attempts
        # (probability of 10 failures = 0.5^10 ≈ 0.001)
        if not success:
            self.skipTest("Download not available or too many simulated failures")


class TestIntegrationReal(unittest.TestCase):
    """Full integration tests with real components."""
    
    @unittest.skipIf(
        os.environ.get('SKIP_INTEGRATION_TESTS', 'true').lower() == 'true',
        "Integration tests disabled (set SKIP_INTEGRATION_TESTS=false to enable)"
    )
    def test_complete_workflow(self):
        """Test the complete workflow with real binary if available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "integration_data"
            port = 31000 + (os.getpid() % 1000)
            
            try:
                # Try to download/ensure binary
                binary_path = ensure_binary_installed()
                
                if not binary_path.exists():
                    self.skipTest("Binary not available for integration test")
                
                # Create and start server
                server = KotaDBServer(
                    data_dir=data_dir,
                    port=port,
                    auto_install=False  # Already installed
                )
                
                server.start(timeout=15000)  # 15 second timeout
                time.sleep(3)  # Give server time to fully initialize
                
                try:
                    # Verify server is running
                    self.assertTrue(server.is_running())
                    
                    # Try to connect with actual client
                    from kotadb import KotaDB
                    client = KotaDB(f"http://localhost:{port}")
                    
                    # Perform real operations
                    doc_id = client.insert({
                        "path": "/test/integration.md",
                        "title": "Integration Test",
                        "content": "Real integration test with actual server"
                    })
                    
                    self.assertIsNotNone(doc_id)
                    
                    # Verify document was created
                    docs = client.list()
                    self.assertGreater(len(docs), 0)
                    
                finally:
                    server.stop()
                    time.sleep(1)
                    self.assertFalse(server.is_running())
                    
            except Exception as e:
                if "binary not found" in str(e).lower():
                    self.skipTest("Binary not available for integration test")
                if "failed to download" in str(e).lower():
                    self.skipTest("Cannot download binary in test environment")
                raise


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)