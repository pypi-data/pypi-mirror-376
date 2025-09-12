# Nebula Client SDK

Official Python SDK for Nebula - Memory, Search, and AI-powered conversations.

## Overview

This SDK provides a unified interface for storing and retrieving memories in Nebula, with support for both conversational and document-based memory storage. The SDK uses the documents endpoint for optimal performance and supports both synchronous and asynchronous operations.

## Installation

```bash
pip install nebula-client
```

## Quick Start

### Basic Setup

```python
from nebula_client import NebulaClient, Memory

# Initialize client
client = NebulaClient(
    api_key="your-api-key",  # or set NEBULA_API_KEY env var
    base_url="https://api.nebulacloud.app"
)
```

### Collection Management

```python
# Create a collection
collection = client.create_cluster(
    name="my_conversations",
    description="Collection for storing conversation memories"
)

# List collections
collections = client.list_clusters()

# Get specific collection
collection = client.get_cluster(collection_id)

# Or get by name (server-side lookup)
collection = client.get_cluster_by_name("my_conversations")

# Update collection
updated_collection = client.update_cluster(
    collection_id,
    name="updated_name",
    description="Updated description"
)

# Delete collection
client.delete_cluster(collection_id)
```

### Storing Memories

#### Individual Memory

```python
# Store a single text document
memory = Memory(
    cluster_id=collection.id,
    content="This is an important memory about machine learning.",
    metadata={"topic": "machine_learning", "importance": "high"}
)

doc_id = client.store_memory(memory)
print(f"Stored document with ID: {doc_id}")
```

#### Conversation Messages

```python
# Store a conversation message
message = Memory(
    cluster_id=collection.id,
    content="What is machine learning?",
    role="user",
    metadata={"timestamp": "2024-01-15T10:30:00Z"}
)

conv_id = client.store_memory(message)
print(f"Stored in conversation: {conv_id}")

# Add a response to the same conversation
response = Memory(
    cluster_id=collection.id,
    content="Machine learning is a subset of AI that enables computers to learn from data.",
    role="assistant",
    parent_id=conv_id,  # Link to existing conversation
    metadata={"timestamp": "2024-01-15T10:30:05Z"}
)

client.store_memory(response)
```

#### Batch Storage

```python
# Store multiple memories at once
memories = [
    Memory(cluster_id=collection.id, content="First memory", metadata={"type": "note"}),
    Memory(cluster_id=collection.id, content="Second memory", metadata={"type": "note"}),
    Memory(cluster_id=collection.id, content="User question", role="user"),
    Memory(cluster_id=collection.id, content="Assistant response", role="assistant", parent_id="conv_123")
]

ids = client.store_memories(memories)
print(f"Stored {len(ids)} memories")
```

### Retrieving Memories

```python
# List memories from a collection
memories = client.list_memories(cluster_ids=[collection.id], limit=10)

for memory in memories:
    print(f"ID: {memory.id}")
    print(f"Content: {memory.content}")
    print(f"Metadata: {memory.metadata}")

# Get specific memory
memory = client.get_memory("memory_id_here")

# List conversations (optionally filter by cluster)
conversations = client.list_conversations(limit=20, cluster_ids=[collection.id])

# Get messages for a conversation, in chronological order
messages = client.get_conversation_messages(conversation_id="conv_123")
```

### Search Across Memories

```python
# Search across collections
results = client.search(
    query="machine learning",
    cluster_ids=[collection.id],
    limit=10,
)

for result in results:
    print(f"Found: {result.content[:100]}...")
    print(f"Score: {result.score}")
```

### Health Check

```python
# Check API health
health = client.health_check()
print(health)
```

## Async Client

The SDK also provides an async client with identical functionality (method names mirror the sync client and return the same shapes):

```python
from nebula_client import AsyncNebulaClient, Memory

async with AsyncNebulaClient(api_key="your-api-key") as client:
    # Store memory
    memory = Memory(cluster_id="cluster_123", content="Async memory")
    doc_id = await client.store_memory(memory)
    
    # Search
    results = await client.search("query", cluster_ids=["cluster_123"])

    # List conversations (optionally filter by cluster)
    conversations = await client.list_conversations(limit=20, cluster_ids=["cluster_123"]) 

    # Get messages for a conversation, in chronological order
    messages = await client.get_conversation_messages(conversation_id="conv_123")

    # Health check
    health = await client.health_check()
```

#### Async search defaults

- The async client enables semantic, fulltext, and hybrid paths by default to return chunk results alongside graph results. Override with `search_settings` if needed:

```python
results = await client.search(
    "query",
    cluster_ids=["cluster_123"],
    search_settings={
        "use_semantic_search": False,
        "use_fulltext_search": False,
        "use_hybrid_search": False,
        "graph_settings": {"enabled": True, "bfs_enabled": True, "bfs_max_depth": 2},
    },
)
```

## API Reference

### Core Methods

#### Cluster (Collection) Management

- `create_cluster(name, description=None, metadata=None)` - Create a new collection
- `get_cluster(cluster_id)` - Get collection details
- `get_cluster_by_name(name)` - Get collection details by name
- `list_clusters(limit=100, offset=0)` - List all collections
- `update_cluster(cluster_id, name=None, description=None, metadata=None)` - Update collection
- `delete_cluster(cluster_id)` - Delete collection

#### Memory Storage

- `store_memory(memory)` - Store a single memory (conversation or document)
- `store_memories(memories)` - Store multiple memories with batching
- `delete(memory_id)` - Delete a memory

#### Memory Retrieval

- `list_memories(cluster_ids, limit=100, offset=0)` - List memories from collections
- `get_memory(memory_id)` - Get specific memory
- `get_conversation_messages(conversation_id)` - Get conversation messages with chronological ordering
- `search(query, cluster_ids, limit=10, retrieval_type=RetrievalType.ADVANCED, filters=None, search_settings=None)` - Search memories

#### Conversations

- `list_conversations(limit=100, offset=0, cluster_ids=None)` - List conversations, optionally filtered by collections

#### Utilities

- `health_check()` - Check API health status

### Data Models

#### Memory (Write Model)

```python
@dataclass
class Memory:
    cluster_id: str
    content: str
    role: Optional[str] = None  # user, assistant, or custom
    parent_id: Optional[str] = None  # conversation_id for messages
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Behavior:**
- `role` present → conversation message
  - `parent_id` used as conversation_id if provided; else a new conversation is created
  - Returns conversation_id
- `role` absent → text/json document
  - Content is stored as raw text
  - Returns document_id

#### MemoryResponse (Read Model)

```python
@dataclass
class MemoryResponse:
    id: str
    content: Optional[str] = None
    chunks: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cluster_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

#### Cluster

```python
@dataclass
class Cluster:
    id: str
    name: str
    description: Optional[str]
    metadata: Dict[str, Any]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    memory_count: int
    owner_id: Optional[str]
```

#### SearchResult

```python
@dataclass
class SearchResult:
    id: str
    score: float
    metadata: Dict[str, Any]
    source: Optional[str]
    content: Optional[str] = None
    # Graph fields for graph search results
    graph_result_type: Optional[GraphSearchResultType] = None
    graph_entity: Optional[GraphEntityResult] = None
    graph_relationship: Optional[GraphRelationshipResult] = None
    graph_community: Optional[GraphCommunityResult] = None
```

## Key Changes from Previous Version

### 1. Unified Write APIs

The SDK now provides unified methods for storing memories:

- `store_memory()` - Single method for both conversations and documents
- `store_memories()` - Batch storage with automatic grouping
- Removed legacy `store()` method

### 2. Memory Model Separation

- `Memory` - Input model for write operations
- `MemoryResponse` - Output model for read operations
- Clear separation of concerns between storage and retrieval

### 3. Conversation Support

Built-in conversation handling:

- Messages with `role` are stored as conversation messages
- Automatic conversation creation and management
- Support for multi-turn conversations
- `get_conversation_messages()` - Direct conversation retrieval with chronological ordering

### 4. Deterministic Document IDs

Documents are created with deterministic IDs based on content hashing:

- Prevents duplicate storage of identical content
- Enables idempotent operations
- Improves data consistency

## Testing

Run the test suite to verify functionality:

```bash
cd py/sdk/nebula_client
pytest tests/ -v
```

The test suite covers:
- Collection management
- Memory storage (individual and batch)
- Memory retrieval
- Search capabilities
- Async client functionality

## Error Handling

The SDK provides specific exception types:

- `NebulaClientException` - General client errors
- `NebulaAuthenticationException` - Authentication failures
- `NebulaRateLimitException` - Rate limiting
- `NebulaValidationException` - Invalid input data
- `NebulaException` - General API errors

## Examples

See the `examples/` directory for complete usage examples including:
- Basic memory storage and retrieval
- Conversation management
- Search and filtering
- Async client usage