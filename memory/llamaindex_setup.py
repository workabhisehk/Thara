"""
LlamaIndex setup for vector store and indexing.
Uses Neon DB PostgreSQL with pgvector for vector storage.
"""
import logging
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from config import settings
import os

logger = logging.getLogger(__name__)

# Initialize embedding model
embed_model = OpenAIEmbedding(
    api_key=settings.openai_api_key,  # OpenAI is now required
    model="text-embedding-3-small"
)

# Set global embedding model
Settings.embed_model = embed_model

# Vector store instance (will be initialized on first use)
vector_store = None
index = None


def get_vector_store() -> PGVectorStore:
    """Get or create vector store instance."""
    global vector_store
    
    if vector_store is None:
        # Parse database URL for connection parameters
        # Format: postgresql://user:password@host:port/database
        from urllib.parse import urlparse
        parsed = urlparse(settings.database_url)
        
        vector_store = PGVectorStore.from_params(
            database=parsed.path[1:],  # Remove leading /
            host=parsed.hostname,
            password=parsed.password,
            port=parsed.port or 5432,
            user=parsed.username,
            table_name="llamaindex_vectors",
            embed_dim=1536,  # OpenAI text-embedding-3-small dimension
        )
        logger.info("Vector store initialized")
    
    return vector_store


def get_index() -> VectorStoreIndex:
    """Get or create vector store index."""
    global index
    
    if index is None:
        storage_context = StorageContext.from_defaults(
            vector_store=get_vector_store()
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store=get_vector_store(),
            storage_context=storage_context
        )
        logger.info("Vector index initialized")
    
    return index


async def init_vector_store():
    """Initialize vector store (create tables if needed)."""
    try:
        store = get_vector_store()
        # The vector store will create tables on first use
        logger.info("Vector store ready")
    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")
        raise

