import redis
from typing import Optional

def initialize_key_if_not_exists(redis_connection_string: str, key: str) -> bool:
    """
    Initializes a Redis key with a value of 0 if the key does not already exist.

    Args:
        redis_connection_string: The connection string for the Redis server.
                                 Format: "redis://[:password]@host:port/db"
        key: The key to check and potentially initialize.

    Returns:
        True if the key was initialized, False otherwise.
    """
    client = redis.from_url(redis_connection_string)
    if not client.exists(key):
        client.set(key, 0)
        return True
    return False