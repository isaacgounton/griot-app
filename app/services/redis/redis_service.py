"""
Redis service for caching and session management.
"""
import os
import json
import logging
from typing import Any, Optional, Dict, List
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for caching and data storage."""
    
    def __init__(self):
        """Initialize Redis service."""
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        
        # Ensure proper redis:// scheme
        if not self.redis_url.startswith(('redis://', 'rediss://', 'unix://')):
            self.redis_url = f"redis://{self.redis_url}"
            
        self.pool = None
        self.redis_client: Optional[Redis] = None
        
        logger.info(f"Redis URL configured")
    
    async def connect(self):
        """Connect to Redis."""
        try:
            # Create Redis client with redis.asyncio
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")
            
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Disconnected from Redis")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except RedisError:
            return False
    
    async def ping(self) -> bool:
        """Ping Redis server to check connectivity."""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.ping()
            return result
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            raise
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            expire: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            # Serialize value to JSON
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            # Set with optional expiration
            if expire:
                result = await self.redis_client.setex(key, expire, serialized_value)
            else:
                result = await self.redis_client.set(key, serialized_value)
            
            logger.debug(f"Set Redis key '{key}' with expiration {expire}")
            return result
        except Exception as e:
            logger.error(f"Error setting Redis key '{key}': {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            default: Default value if key doesn't exist
            
        Returns:
            Value from Redis or default
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return default
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error getting Redis key '{key}': {e}")
            return default
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            result = await self.redis_client.delete(key)
            logger.debug(f"Deleted Redis key '{key}'")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting Redis key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Redis key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking Redis key '{key}': {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            seconds: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            result = await self.redis_client.expire(key, seconds)
            logger.debug(f"Set expiration for Redis key '{key}' to {seconds} seconds")
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting expiration for Redis key '{key}': {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (default: "*" for all keys)
            
        Returns:
            List of matching keys
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return []
        
        try:
            keys = await self.redis_client.keys(pattern)
            return keys if keys else []
        except Exception as e:
            logger.error(f"Error getting Redis keys with pattern '{pattern}': {e}")
            return []
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """
        Alias for keys method - for admin dashboard compatibility.
        """
        return await self.keys(pattern)
    
    async def flushdb(self) -> bool:
        """
        Flush current database.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.info("Flushed Redis database")
            return True
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False
    
    # Job queue specific methods
    async def enqueue_job(self, queue_name: str, job_data: Dict[str, Any]) -> bool:
        """
        Enqueue a job to a Redis list.
        
        Args:
            queue_name: Name of the queue
            job_data: Job data to enqueue
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            serialized_job = json.dumps(job_data)
            # Redis async operations - type ignore due to redis library type stub issues
            await self.redis_client.lpush(queue_name, serialized_job)  # type: ignore
            logger.debug(f"Enqueued job to '{queue_name}': {job_data.get('job_id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error enqueuing job to '{queue_name}': {e}")
            return False
    
    async def dequeue_job(self, queue_name: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """
        Dequeue a job from a Redis list.
        
        Args:
            queue_name: Name of the queue
            timeout: Timeout in seconds for blocking pop
            
        Returns:
            Job data or None if no job available
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return None
        
        try:
            # Redis async operations - type ignore due to redis library type stub issues
            result = await self.redis_client.brpop([queue_name], timeout=timeout)  # type: ignore
            if result:
                _, job_data = result
                job = json.loads(job_data)
                logger.debug(f"Dequeued job from '{queue_name}': {job.get('job_id', 'unknown')}")
                return job
            return None
        except Exception as e:
            logger.error(f"Error dequeuing job from '{queue_name}': {e}")
            return None
    
    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get the length of a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Queue length
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return 0
        
        try:
            # Redis async operations - type ignore due to redis library type stub issues
            length = await self.redis_client.llen(queue_name)  # type: ignore
            return int(length)
        except Exception as e:
            logger.error(f"Error getting queue length for '{queue_name}': {e}")
            return 0

# Create a singleton instance
redis_service = RedisService()

# Async context manager for Redis operations
async def get_redis():
    """Get Redis service instance with connection."""
    if not await redis_service.is_connected():
        await redis_service.connect()
    return redis_service