# KotaDB Python Client

A simple, PostgreSQL-level easy-to-use Python client for KotaDB with type safety and builder patterns.

[![PyPI version](https://badge.fury.io/py/kotadb-client.svg)](https://pypi.org/project/kotadb-client/)

## Features

- **Type Safety**: Runtime-validated types (`ValidatedPath`, `ValidatedDocumentId`, etc.)
- **Builder Patterns**: Fluent APIs for safe document and query construction
- **Full API Coverage**: Support for all KotaDB operations (CRUD, search, metadata)
- **Connection Management**: Automatic retries, connection pooling, timeout handling
- **Multiple Search Types**: Text, semantic, and hybrid search capabilities

## Installation

```bash
pip install kotadb-client
```

## Quick Start

```python
from kotadb import KotaDB

# Connect to KotaDB
db = KotaDB("http://localhost:8080")

# Insert a document
doc_id = db.insert({
    "path": "/notes/meeting.md",
    "title": "Team Meeting Notes",
    "content": "Discussed project roadmap and next steps...",
    "tags": ["work", "meeting", "planning"]
})

# Search for documents
results = db.query("project roadmap")
for result in results.results:
    print(f"Found: {result.document.title} (score: {result.score})")

# Get a specific document
doc = db.get(doc_id)
print(f"Document: {doc.title}")

# Update a document
updated_doc = db.update(doc_id, {
    "content": "Updated meeting notes with action items..."
})

# Delete a document
db.delete(doc_id)
```

## Type Safety & Builder Patterns

### Validated Types
Prevent errors at runtime with validated types that mirror the Rust implementation:

```python
from kotadb import ValidatedPath, ValidatedDocumentId, ValidatedTitle

# These will raise ValidationError if invalid
path = ValidatedPath("/notes/meeting.md")  # Validates: no null bytes, no parent dir refs, etc.
doc_id = ValidatedDocumentId.parse("123e4567-e89b-12d3-a456-426614174000")
title = ValidatedTitle("My Document Title")  # Validates: non-empty, length limits

# Use in document operations
db.insert({
    "path": path.as_str(),
    "title": title.as_str(), 
    "content": "Document content..."
})
```

### Document Builder Pattern
Build documents safely with validation at each step:

```python
from kotadb import DocumentBuilder

# Fluent API with validation
doc_id = db.insert_with_builder(
    DocumentBuilder()
    .path("/knowledge/python-guide.md")
    .title("Python Best Practices")
    .content("# Python Guide\n\nBest practices for Python development...")
    .add_tag("python")
    .add_tag("documentation")
    .add_metadata("author", "user@example.com")
    .add_metadata("priority", "high")
)
```

### Query Builder Pattern
Build complex queries with type safety:

```python
from kotadb import QueryBuilder

# Text search with filters
results = db.query_with_builder(
    QueryBuilder()
    .text("machine learning algorithms")
    .limit(20)
    .offset(10)
    .tag_filter("ai")
    .path_filter("/research/*")
)

# Semantic search
results = db.semantic_search_with_builder(
    QueryBuilder()
    .text("neural network architectures")
    .limit(10)
)

# Hybrid search
results = db.hybrid_search_with_builder(
    QueryBuilder()
    .text("database optimization techniques")
    .semantic_weight(0.8)  # 80% semantic, 20% text
    .limit(15)
)
```

### Update Builder Pattern
Safely update documents with fine-grained control:

```python
from kotadb import UpdateBuilder

# Update with builder pattern
updated_doc = db.update_with_builder(doc_id,
    UpdateBuilder()
    .title("Updated Python Guide")
    .add_tag("updated")
    .add_tag("2024")
    .remove_tag("draft")
    .add_metadata("last_modified_by", "user123")
    .add_metadata("version", "2.0")
)
```

## Connection Options

### Environment Variable
```bash
export KOTADB_URL="http://localhost:8080"
```

```python
# Will use KOTADB_URL automatically
db = KotaDB()
```

### Connection String
```python
# PostgreSQL-style connection string
db = KotaDB("kotadb://localhost:8080/myapp")

# Direct HTTP URL
db = KotaDB("http://localhost:8080")
```

### Context Manager
```python
with KotaDB("http://localhost:8080") as db:
    results = db.query("search term")
    # Connection automatically closed
```

## Search Options

### Text Search
```python
results = db.query("rust programming patterns", limit=10)
```

### Semantic Search
```python
results = db.semantic_search("machine learning concepts", limit=5)
```

### Hybrid Search
```python
results = db.hybrid_search(
    "database optimization",
    limit=10,
    semantic_weight=0.7  # 70% semantic, 30% text
)
```

## Document Operations

### Create Document
```python
# Using dictionary
doc_id = db.insert({
    "path": "/docs/guide.md",
    "title": "User Guide",
    "content": "How to use the system...",
    "tags": ["documentation", "guide"],
    "metadata": {"author": "jane@example.com"}
})

# Using CreateDocumentRequest
from kotadb.types import CreateDocumentRequest

doc_request = CreateDocumentRequest(
    path="/docs/api.md",
    title="API Documentation",
    content="API endpoints and usage...",
    tags=["api", "docs"]
)
doc_id = db.insert(doc_request)
```

### List Documents
```python
# Get all documents
all_docs = db.list_all()

# With pagination
docs = db.list_all(limit=50, offset=100)
```

### Database Health
```python
# Check health
health = db.health()
print(f"Status: {health['status']}")

# Get statistics
stats = db.stats()
print(f"Document count: {stats['document_count']}")
```

## Error Handling

```python
from kotadb.exceptions import KotaDBError, NotFoundError, ConnectionError

try:
    doc = db.get("non-existent-id")
except NotFoundError:
    print("Document not found")
except ConnectionError:
    print("Failed to connect to database")
except KotaDBError as e:
    print(f"Database error: {e}")
```

## Configuration

```python
db = KotaDB(
    url="http://localhost:8080",
    timeout=30,  # Request timeout in seconds
    retries=3    # Number of retry attempts
)
```

## Data Types

### Core Types
```python
@dataclass
class Document:
    id: str
    path: str
    title: str
    content: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    size: int
    metadata: Optional[Dict[str, Any]]

@dataclass
class QueryResult:
    results: List[Document]
    total_count: int
    query_time_ms: Optional[int]
```

### Validated Types
```python
class ValidatedPath:
    """Path with validation for safety (no traversal, null bytes, etc.)"""
    def __init__(self, path: str) -> None: ...
    def as_str(self) -> str: ...

class ValidatedDocumentId:
    """Document ID with UUID validation"""
    @classmethod
    def new(cls) -> 'ValidatedDocumentId': ...
    @classmethod
    def parse(cls, s: str) -> 'ValidatedDocumentId': ...
    def as_str(self) -> str: ...

class ValidatedTitle:
    """Title with length and content validation"""
    def __init__(self, title: str) -> None: ...
    def as_str(self) -> str: ...

class ValidatedTimestamp:
    """Timestamp with range validation"""
    @classmethod
    def now(cls) -> 'ValidatedTimestamp': ...
    def as_secs(self) -> int: ...

class NonZeroSize:
    """Size value that must be positive"""
    def __init__(self, size: int) -> None: ...
    def get(self) -> int: ...
```

### Builder Types
```python
class DocumentBuilder:
    """Fluent API for safe document construction"""
    def path(self, path: Union[str, ValidatedPath]) -> 'DocumentBuilder': ...
    def title(self, title: Union[str, ValidatedTitle]) -> 'DocumentBuilder': ...
    def content(self, content: Union[str, bytes, List[int]]) -> 'DocumentBuilder': ...
    def add_tag(self, tag: str) -> 'DocumentBuilder': ...
    def add_metadata(self, key: str, value: Any) -> 'DocumentBuilder': ...
    def build(self) -> CreateDocumentRequest: ...

class QueryBuilder:
    """Fluent API for building search queries"""
    def text(self, query: str) -> 'QueryBuilder': ...
    def limit(self, limit: int) -> 'QueryBuilder': ...
    def offset(self, offset: int) -> 'QueryBuilder': ...
    def tag_filter(self, tag: str) -> 'QueryBuilder': ...
    def build(self) -> Dict[str, Any]: ...

class UpdateBuilder:
    """Fluent API for safe document updates"""
    def title(self, title: Union[str, ValidatedTitle]) -> 'UpdateBuilder': ...
    def content(self, content: Union[str, bytes, List[int]]) -> 'UpdateBuilder': ...
    def add_tag(self, tag: str) -> 'UpdateBuilder': ...
    def remove_tag(self, tag: str) -> 'UpdateBuilder': ...
    def add_metadata(self, key: str, value: Any) -> 'UpdateBuilder': ...
    def build(self) -> Dict[str, Any]: ...
```

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Format code:
```bash
black kotadb/
```

Type checking:
```bash
mypy kotadb/
```

## License

MIT License - see LICENSE file for details.

## Contributing

See CONTRIBUTING.md for contribution guidelines.

## Support

- GitHub Issues: https://github.com/jayminwest/kota-db/issues
- Documentation: https://github.com/jayminwest/kota-db/docs
