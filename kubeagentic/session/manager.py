"""Session manager for handling conversations."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from kubeagentic.exceptions import SessionError
from kubeagentic.session.storage import (
    SessionStorage,
    InMemoryStorage,
    RedisStorage,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage user sessions and conversation history."""

    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        storage_type: str = "memory",
        redis_url: Optional[str] = None,
        session_ttl: int = 3600,
    ):
        """
        Initialize session manager.
        
        Args:
            storage: Custom storage backend
            storage_type: Storage type ('memory' or 'redis')
            redis_url: Redis URL (if using Redis storage)
            session_ttl: Session time-to-live in seconds
        """
        if storage:
            self.storage = storage
        elif storage_type == "redis":
            if not redis_url:
                redis_url = "redis://localhost:6379"
            self.storage = RedisStorage(redis_url=redis_url, ttl_seconds=session_ttl)
        else:
            self.storage = InMemoryStorage(ttl_seconds=session_ttl)
        
        logger.info(f"SessionManager initialized with {storage_type} storage")

    async def create_session(
        self,
        agent_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new session.
        
        Args:
            agent_name: Name of the agent
            user_id: Optional user identifier
            session_id: Optional custom session ID
            metadata: Optional metadata
            
        Returns:
            Session ID
            
        Raises:
            SessionError: If session creation fails
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            await self.storage.create_session(
                session_id=session_id,
                agent_name=agent_name,
                user_id=user_id,
                metadata=metadata,
            )
            
            logger.info(f"Session created: {session_id} for agent: {agent_name}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionError(f"Failed to create session: {e}") from e

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            return await self.storage.get_session(session_id)
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise SessionError(f"Failed to get session: {e}") from e

    async def update_session(
        self, session_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update session data.
        
        Args:
            session_id: Session ID
            data: Data to update
            
        Returns:
            Updated session data
            
        Raises:
            SessionError: If session not found or update fails
        """
        try:
            return await self.storage.update_session(session_id, data)
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise SessionError(f"Failed to update session: {e}") from e

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.storage.delete_session(session_id)
            if result:
                logger.info(f"Session deleted: {session_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise SessionError(f"Failed to delete session: {e}") from e

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to session history.
        
        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata
            
        Raises:
            SessionError: If session not found or add fails
        """
        try:
            await self.storage.add_message(
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata,
            )
            logger.debug(f"Message added to session {session_id}: {role}")
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            raise SessionError(f"Failed to add message: {e}") from e

    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
            include_system: Whether to include system messages
            
        Returns:
            List of messages
            
        Raises:
            SessionError: If session not found or retrieval fails
        """
        try:
            messages = await self.storage.get_messages(session_id, limit)
            
            if not include_system:
                messages = [m for m in messages if m["role"] != "system"]
            
            return messages
        except Exception as e:
            logger.error(f"Failed to get history for session {session_id}: {e}")
            raise SessionError(f"Failed to get conversation history: {e}") from e

    async def clear_conversation(self, session_id: str) -> None:
        """
        Clear conversation history but keep session.
        
        Args:
            session_id: Session ID
            
        Raises:
            SessionError: If session not found or clear fails
        """
        try:
            await self.storage.clear_messages(session_id)
            logger.info(f"Conversation cleared for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear conversation for session {session_id}: {e}")
            raise SessionError(f"Failed to clear conversation: {e}") from e

    async def get_context_for_llm(
        self,
        session_id: str,
        max_messages: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Get formatted conversation history for LLM context.
        
        Args:
            session_id: Session ID
            max_messages: Maximum number of messages to include
            
        Returns:
            List of messages in LLM format [{"role": "...", "content": "..."}]
        """
        try:
            messages = await self.get_conversation_history(session_id, limit=max_messages)
            
            # Format for LLM
            formatted = []
            for msg in messages:
                formatted.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
            
            return formatted
        except Exception as e:
            logger.error(f"Failed to get LLM context for session {session_id}: {e}")
            # Return empty context on error
            return []

    async def close(self):
        """Close storage backend connections."""
        if hasattr(self.storage, 'close'):
            await self.storage.close()
            logger.info("Session storage closed") 