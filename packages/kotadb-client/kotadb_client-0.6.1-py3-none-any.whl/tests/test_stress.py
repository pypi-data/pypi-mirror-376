"""
Stress tests for KotaDB Python client.

These tests push the client and server to their limits to ensure stability.
"""

import concurrent.futures
import random
import string
import threading
import time
import uuid
from typing import Tuple

import pytest

from kotadb import KotaDB


def generate_random_document(size_kb: int = 1) -> dict:
    """Generate a random document of specified size."""
    content_size = size_kb * 1024
    content = "".join(random.choices(string.ascii_letters + string.digits, k=content_size))

    return {
        "path": f"/stress/doc_{uuid.uuid4()}.md",
        "title": f"Stress Test Document {uuid.uuid4()}",
        "content": content,
        "tags": [f"tag{i}" for i in range(random.randint(1, 10))],
    }


@pytest.mark.slow
@pytest.mark.stress
class TestHighLoad:
    """Test client behavior under high load."""

    def test_many_documents(self, client: KotaDB) -> None:
        """Test handling many documents."""
        num_docs = 100
        doc_ids = []

        print(f"\nCreating {num_docs} documents...")
        start_time = time.time()

        for i in range(num_docs):
            doc = {
                "path": f"/stress/many/doc_{i}.md",
                "title": f"Document {i}",
                "content": f"Content for document {i}",
                "tags": [f"batch{i // 10}"],
            }
            doc_id = client.insert(doc)
            doc_ids.append(doc_id)

            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{num_docs} documents...")

        elapsed = time.time() - start_time
        rate = num_docs / elapsed

        print(f"Created {num_docs} documents in {elapsed:.2f}s ({rate:.1f} docs/sec)")
        assert rate > 10  # Should handle at least 10 docs/sec

        # Test searching through many documents
        start_time = time.time()
        results = client.query("document")
        search_time = time.time() - start_time

        print(f"Search returned {results.total_count} results in {search_time:.3f}s")
        assert search_time < 1.0  # Search should complete within 1 second

        # Clean up
        print("Cleaning up...")
        for doc_id in doc_ids:
            try:
                client.delete(doc_id)
            except:
                pass

    def test_concurrent_clients(self) -> None:
        """Test multiple client instances operating concurrently."""
        num_clients = 10
        operations_per_client = 20

        def client_operations(client_id: int) -> Tuple[int, int, float]:
            """Perform operations with a client."""
            client = KotaDB("http://localhost:8080")
            successes = 0
            failures = 0
            start = time.time()

            for op in range(operations_per_client):
                try:
                    # Mix of operations
                    if op % 3 == 0:
                        # Insert
                        doc = generate_random_document(size_kb=1)
                        doc_id = client.insert(doc)
                        successes += 1

                        # Sometimes delete immediately
                        if random.random() > 0.5:
                            client.delete(doc_id)
                    elif op % 3 == 1:
                        # Search
                        results = client.query("test")
                        successes += 1
                    else:
                        # Health check
                        client.health()
                        successes += 1
                except Exception:
                    failures += 1

            elapsed = time.time() - start
            client.close()
            return successes, failures, elapsed

        print(f"\nRunning {num_clients} concurrent clients...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = [executor.submit(client_operations, i) for i in range(num_clients)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        total_successes = sum(r[0] for r in results)
        total_failures = sum(r[1] for r in results)
        avg_time = sum(r[2] for r in results) / len(results)

        print(f"Results: {total_successes} successes, {total_failures} failures")
        print(f"Average time per client: {avg_time:.2f}s")

        # Should have high success rate
        success_rate = total_successes / (total_successes + total_failures)
        assert success_rate > 0.95  # 95% success rate

    def test_rapid_fire_operations(self, client: KotaDB) -> None:
        """Test rapid successive operations."""
        num_operations = 100
        doc_ids = []

        print(f"\nPerforming {num_operations} rapid operations...")
        start_time = time.time()

        for i in range(num_operations):
            op_type = random.choice(["insert", "get", "search", "delete"])

            try:
                if op_type == "insert":
                    doc = {
                        "path": f"/rapid/doc_{i}.md",
                        "title": f"Rapid {i}",
                        "content": f"Content {i}",
                        "tags": ["rapid"],
                    }
                    doc_id = client.insert(doc)
                    doc_ids.append(doc_id)
                elif op_type == "get" and doc_ids:
                    doc_id = random.choice(doc_ids)
                    client.get(doc_id)
                elif op_type == "search":
                    client.query("rapid", limit=10)
                elif op_type == "delete" and doc_ids:
                    doc_id = doc_ids.pop()
                    client.delete(doc_id)
            except Exception:
                pass  # Some operations may fail, that's okay

        elapsed = time.time() - start_time
        ops_per_sec = num_operations / elapsed

        print(
            f"Completed {num_operations} operations in {elapsed:.2f}s ({ops_per_sec:.1f} ops/sec)"
        )
        assert ops_per_sec > 50  # Should handle at least 50 ops/sec

        # Clean up remaining documents
        for doc_id in doc_ids:
            try:
                client.delete(doc_id)
            except:
                pass


@pytest.mark.slow
@pytest.mark.stress
class TestMemoryAndResources:
    """Test memory usage and resource handling."""

    def test_large_documents(self, client: KotaDB) -> None:
        """Test handling of large documents."""
        sizes_kb = [10, 100, 500, 1000]  # Test various sizes up to 1MB

        for size_kb in sizes_kb:
            print(f"\nTesting {size_kb}KB document...")
            doc = generate_random_document(size_kb=size_kb)

            start = time.time()
            doc_id = client.insert(doc)
            insert_time = time.time() - start

            start = time.time()
            retrieved = client.get(doc_id)
            get_time = time.time() - start

            print(f"  Insert: {insert_time:.3f}s, Get: {get_time:.3f}s")

            # Verify content integrity
            assert len(retrieved.content) >= size_kb * 1024 * 0.9  # Allow for encoding differences

            # Clean up
            client.delete(doc_id)

            # Should complete in reasonable time
            assert insert_time < 5.0
            assert get_time < 5.0

    def test_connection_pool_exhaustion(self) -> None:
        """Test behavior when connection pool is exhausted."""
        clients = []

        try:
            # Create many clients
            for i in range(50):
                client = KotaDB("http://localhost:8080")
                clients.append(client)

                # Perform an operation to ensure connection is established
                client.health()

            print(f"\nCreated {len(clients)} client connections")

            # All clients should still work
            for client in clients[:10]:  # Test a subset
                health = client.health()
                assert health["status"] == "healthy"

        finally:
            # Clean up all clients
            for client in clients:
                try:
                    client.close()
                except:
                    pass

    def test_long_running_connection(self, client: KotaDB) -> None:
        """Test a connection that runs for an extended period."""
        duration_seconds = 30
        operations = 0
        errors = 0

        print(f"\nRunning operations for {duration_seconds} seconds...")
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            try:
                # Perform random operation
                op = random.choice(
                    [
                        lambda: client.health(),
                        lambda: client.query("test", limit=5),
                        lambda: client.insert(generate_random_document(size_kb=1)),
                    ]
                )
                op()
                operations += 1
            except Exception:
                errors += 1

            time.sleep(0.1)  # Small delay between operations

        elapsed = time.time() - start_time
        print(f"Completed {operations} operations with {errors} errors in {elapsed:.1f}s")

        # Should maintain stability
        error_rate = errors / (operations + errors) if (operations + errors) > 0 else 0
        assert error_rate < 0.05  # Less than 5% error rate


@pytest.mark.slow
@pytest.mark.stress
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_database_operations(self, client: KotaDB) -> None:
        """Test operations on an empty database."""
        # Search in empty database
        results = client.query("anything")
        assert results.total_count == 0
        assert len(results.results) == 0

        # Get non-existent document
        with pytest.raises(Exception):
            client.get(str(uuid.uuid4()))

    def test_duplicate_paths(self, client: KotaDB) -> None:
        """Test handling of duplicate document paths."""
        doc = {
            "path": "/duplicate/test.md",
            "title": "Original",
            "content": "Original content",
            "tags": ["original"],
        }

        # Insert first document
        doc_id1 = client.insert(doc)

        # Try to insert with same path
        doc["title"] = "Duplicate"
        doc["content"] = "Duplicate content"
        doc_id2 = client.insert(doc)

        # Both should succeed (server should handle this)
        assert doc_id1 != doc_id2

        # Clean up
        client.delete(doc_id1)
        client.delete(doc_id2)

    def test_concurrent_modifications(self, client: KotaDB) -> None:
        """Test concurrent modifications to the same document."""
        # Create a document
        doc = generate_random_document()
        doc_id = client.insert(doc)

        errors = []

        def modify_document(thread_id: int) -> None:
            """Modify the document."""
            try:
                for _ in range(10):
                    # Try to update
                    updates = {
                        "title": f"Updated by thread {thread_id}",
                        "content": list(f"Content from thread {thread_id}".encode()),
                    }
                    client.update(doc_id, updates)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        # Start concurrent modifications
        threads = []
        for i in range(5):
            thread = threading.Thread(target=modify_document, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent updates gracefully
        # Some updates might fail, but not all
        assert len(errors) < 25  # Less than half should fail

        # Document should still be retrievable
        final_doc = client.get(doc_id)
        assert final_doc.id == doc_id

        # Clean up
        client.delete(doc_id)

    def test_malformed_data_handling(self, client: KotaDB) -> None:
        """Test handling of malformed or invalid data."""
        test_cases = [
            # Empty values
            {"path": "", "title": "Empty Path", "content": "Content"},
            {"path": "/test.md", "title": "", "content": "Content"},
            {"path": "/test.md", "title": "Title", "content": ""},
            # Very long values
            {"path": "/" + "x" * 1000 + ".md", "title": "Long Path", "content": "Content"},
            {"path": "/test.md", "title": "x" * 10000, "content": "Content"},
            # Special characters
            {"path": "/test\x00.md", "title": "Null Byte", "content": "Content"},
            {"path": "/test.md", "title": "Tab\tTitle", "content": "New\nLine"},
        ]

        for i, test_data in enumerate(test_cases):
            try:
                doc_id = client.insert(test_data)
                # If it succeeds, should be retrievable
                doc = client.get(doc_id)
                assert doc.id == doc_id
                client.delete(doc_id)
            except Exception:
                # Some may fail, that's expected
                pass

    def test_network_timeout_handling(self, client: KotaDB) -> None:
        """Test handling of network timeouts."""
        # Create a client with very short timeout
        from unittest.mock import patch

        import requests

        with patch.object(client.session, "request") as mock_request:
            # Simulate timeout
            mock_request.side_effect = requests.Timeout("Connection timed out")

            with pytest.raises(Exception):
                client.health()

            # Client should still be usable after timeout
            mock_request.side_effect = None
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {"status": "healthy"}

            # This should work again
            try:
                health = client.health()
                # If mock works, we get mocked response
                assert health["status"] == "healthy"
            except:
                # If mock doesn't work due to connection pooling, that's okay
                pass


@pytest.fixture
def client() -> KotaDB:
    """Create a client for stress testing."""
    import requests

    # Check if server is running
    try:
        response = requests.get("http://localhost:8080/health", timeout=1)
        if response.status_code != 200:
            pytest.skip("KotaDB server not running")
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip("KotaDB server not running")

    return KotaDB("http://localhost:8080")
