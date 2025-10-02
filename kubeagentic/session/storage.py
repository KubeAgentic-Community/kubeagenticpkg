"""Session storage backends for conversation history."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionStorage(ABC):
    """Abstract base class for session storage."""

    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        agent_name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new session."""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        pass

    @abstractmethod
    async def update_session(
        self, session_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session data."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to session history."""
        pass

    @abstractmethod
    async def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get message history for a session."""
        pass

    @abstractmethod
    async def clear_messages(self, session_id: str) -> None:
        """Clear message history for a session."""
        pass


class InMemoryStorage(SessionStorage):
    """In-memory session storage (not persistent)."""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize in-memory storage.
        
        Args:
            ttl_seconds: Session time-to-live in seconds
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.ttl_seconds = ttl_seconds
        logger.info("InMemoryStorage initialized")

    async def create_session(
        self,
        session_id: str,
        agent_name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new session."""
        session = {
            "session_id": session_id,
            "agent_name": agent_name,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
            ).isoformat(),
        }
        self.sessions[session_id] = session
        self.messages[session_id] = []
        logger.debug(f"Session created: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        session = self.sessions.get(session_id)
        if session:
            # Check expiry
            expires_at = datetime.fromisoformat(session["expires_at"])
            if datetime.utcnow() > expires_at:
                await self.delete_session(session_id)
                return None
        return session

    async def update_session(
        self, session_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session data."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.update(data)
        session["updated_at"] = datetime.utcnow().isoformat()
        self.sessions[session_id] = session
        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.messages:
                del self.messages[session_id]
            logger.debug(f"Session deleted: {session_id}")
            return True
        return False

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to session history."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if session_id not in self.messages:
            self.messages[session_id] = []
        
        self.messages[session_id].append(message)
        
        # Update session timestamp
        session["updated_at"] = datetime.utcnow().isoformat()
        logger.debug(f"Message added to session: {session_id}")

    async def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get message history for a session."""
        messages = self.messages.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    async def clear_messages(self, session_id: str) -> None:
        """Clear message history for a session."""
        if session_id in self.messages:
            self.messages[session_id] = []
            logger.debug(f"Messages cleared for session: {session_id}")


class RedisStorage(SessionStorage):
    """Redis-based session storage (persistent)."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,
        key_prefix: str = "kubeagentic:session:",
    ):
        """
        Initialize Redis storage.
        
        Args:
            redis_url: Redis connection URL
            ttl_seconds: Session time-to-live in seconds
            key_prefix: Key prefix for Redis keys
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._redis = None
        logger.info(f"RedisStorage initialized with URL: {redis_url}")

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis

    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"{self.key_prefix}{session_id}"

    def _messages_key(self, session_id: str) -> str:
        """Get Redis key for messages."""
        return f"{self.key_prefix}{session_id}:messages"

    async def create_session(
        self,
        session_id: str,
        agent_name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new session."""
        redis = await self._get_redis()
        
        session = {
            "session_id": session_id,
            "agent_name": agent_name,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        key = self._session_key(session_id)
        await redis.setex(
            key,
            self.ttl_seconds,
            json.dumps(session),
        )
        logger.debug(f"Session created in Redis: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        redis = await self._get_redis()
        key = self._session_key(session_id)
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def update_session(
        self, session_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session data."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.update(data)
        session["updated_at"] = datetime.utcnow().isoformat()
        
        redis = await self._get_redis()
        key = self._session_key(session_id)
        await redis.setex(
            key,
            self.ttl_seconds,
            json.dumps(session),
        )
        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        redis = await self._get_redis()
        key = self._session_key(session_id)
        messages_key = self._messages_key(session_id)
        
        result = await redis.delete(key, messages_key)
        logger.debug(f"Session deleted from Redis: {session_id}")
        return result > 0

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to session history."""
        redis = await self._get_redis()
        
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        messages_key = self._messages_key(session_id)
        await redis.rpush(messages_key, json.dumps(message))
        await redis.expire(messages_key, self.ttl_seconds)
        
        # Update session timestamp
        await self.update_session(session_id, {})
        logger.debug(f"Message added to Redis session: {session_id}")

    async def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get message history for a session."""
        redis = await self._get_redis()
        messages_key = self._messages_key(session_id)
        
        if limit:
            raw_messages = await redis.lrange(messages_key, -limit, -1)
        else:
            raw_messages = await redis.lrange(messages_key, 0, -1)
        
        return [json.loads(msg) for msg in raw_messages]

    async def clear_messages(self, session_id: str) -> None:
        """Clear message history for a session."""
        redis = await self._get_redis()
        messages_key = self._messages_key(session_id)
        await redis.delete(messages_key)
        logger.debug(f"Messages cleared in Redis for session: {session_id}")

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed") 