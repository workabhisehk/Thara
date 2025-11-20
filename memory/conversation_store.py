"""
Store and retrieve conversations using LlamaIndex.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from llama_index.core import Document
from llama_index.core.schema import NodeWithScore
from memory.llamaindex_setup import get_index
from database.models import Conversation, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def store_conversation(
    session: AsyncSession,
    user_id: int,
    message_id: int,
    text: str,
    is_from_user: bool,
    intent: Optional[str] = None,
    entities: Optional[Dict[str, Any]] = None
) -> Conversation:
    """
    Store a conversation message in both PostgreSQL and vector store.
    
    Args:
        session: Database session
        user_id: User ID
        message_id: Telegram message ID
        text: Message text
        is_from_user: True if from user, False if from bot
        intent: Extracted intent (optional)
        entities: Extracted entities (optional)
    
    Returns:
        Created Conversation object
    """
    # Store in PostgreSQL
    conversation = Conversation(
        user_id=user_id,
        message_id=message_id,
        text=text,
        is_from_user=is_from_user,
        intent=intent,
        entities=entities
    )
    session.add(conversation)
    await session.flush()
    
    # Store in vector store for semantic search
    try:
        index = get_index()
        
        # Create document with metadata
        doc = Document(
            text=text,
            metadata={
                "conversation_id": conversation.id,
                "user_id": user_id,
                "message_id": message_id,
                "is_from_user": is_from_user,
                "intent": intent or "",
                "timestamp": conversation.created_at.isoformat() if conversation.created_at else datetime.utcnow().isoformat()
            }
        )
        
        # Insert into index
        index.insert(doc)
        logger.debug(f"Stored conversation {conversation.id} in vector store")
    except Exception as e:
        logger.error(f"Error storing conversation in vector store: {e}")
        # Don't fail if vector store fails, PostgreSQL is primary
    
    return conversation


async def retrieve_relevant_conversations(
    user_id: int,
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant conversations using semantic search.
    
    Args:
        user_id: User ID to filter by
        query: Search query
        limit: Maximum number of results
    
    Returns:
        List of relevant conversations with scores
    """
    try:
        index = get_index()
        query_engine = index.as_query_engine(similarity_top_k=limit * 2)  # Get more, filter by user
        
        # Query
        response = query_engine.query(query)
        
        # Filter by user_id and format results
        results = []
        for node in response.source_nodes:
            if isinstance(node, NodeWithScore):
                metadata = node.node.metadata
                if metadata.get("user_id") == user_id:
                    results.append({
                        "text": node.node.text,
                        "score": node.score,
                        "metadata": metadata,
                        "conversation_id": metadata.get("conversation_id")
                    })
                    if len(results) >= limit:
                        break
        
        return results
    except Exception as e:
        logger.error(f"Error retrieving conversations: {e}")
        return []


async def get_recent_conversations(
    session: AsyncSession,
    user_id: int,
    limit: int = 10
) -> List[Conversation]:
    """
    Get recent conversations from PostgreSQL.
    
    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of results
    
    Returns:
        List of Conversation objects
    """
    stmt = select(Conversation).where(
        Conversation.user_id == user_id
    ).order_by(
        Conversation.created_at.desc()
    ).limit(limit)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())

