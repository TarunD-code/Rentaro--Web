import os
import json
import logging
from typing import Optional, Any

# Setup centralized logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shared_redis")

# MANUALLY LOAD .ENV IF EXISTS
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# ENVIRONMENT CONFIG
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

# Dynamically override Redis host/port/password if REDIS_URL is provided
if REDIS_URL:
    from urllib.parse import urlparse
    try:
        parsed_url = urlparse(REDIS_URL)
        if parsed_url.hostname:
            REDIS_HOST = parsed_url.hostname
        if parsed_url.port:
            REDIS_PORT = parsed_url.port
        if parsed_url.password:
            REDIS_PASSWORD = parsed_url.password
    except Exception as parse_err:
        logger.warning(f"Failed to parse REDIS_URL: {parse_err}")

# LAZY CLIENT INITIALIZER
_redis_client = None
_use_fallback = False
_memory_cache = {}  # Resilient in-memory fallback cache

def _get_redis_client():
    global _redis_client, _use_fallback
    if _redis_client is not None:
        return _redis_client
        
    if _use_fallback:
        return None
        
    is_production = os.environ.get("ENV", "development").lower() == "production"
        
    try:
        import redis
        logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
        
        # Configure connection pool
        pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0
        )
        _redis_client = redis.Redis(connection_pool=pool)
        # Ping check
        _redis_client.ping()
        logger.info("✅ Connected to Redis successfully!")
        return _redis_client
    except Exception as e:
        if is_production:
            logger.error(f"❌ FATAL: Redis connection failed in PRODUCTION mode: {e}")
            raise ConnectionError(f"Redis connection failed in production: {e}")
            
        logger.warning(f"Failed to connect to Redis: {e}. Gracefully falling back to in-memory caching.")
        _use_fallback = True
        return None


# CORE CACHE API
def get(key: str) -> Optional[str]:
    """ Retrieves key value from Redis or local in-memory fallback. """
    client = _get_redis_client()
    if client is not None:
        try:
            val = client.get(key)
            if val:
                logger.info(f"[Redis Cache HIT] Key: {key}")
            else:
                logger.info(f"[Redis Cache MISS] Key: {key}")
            return val
        except Exception as e:
            logger.warning(f"Redis get failed: {e}. Reading from in-memory fallback.")
            
    # Read from in-memory dictionary
    if key in _memory_cache:
        import time
        val, expiry = _memory_cache[key]
        if expiry is None or expiry > time.time():
            logger.info(f"[InMemory Cache HIT] Key: {key}")
            return val
        else:
            # Expired
            logger.info(f"[InMemory Cache EXPIRED] Key: {key}")
            del _memory_cache[key]
    logger.info(f"[InMemory Cache MISS] Key: {key}")
    return None

def set(key: str, value: str, ttl: int = None) -> bool:
    """ Sets key value with an optional TTL in seconds. """
    client = _get_redis_client()
    if client is not None:
        try:
            if ttl:
                client.set(key, value, ex=ttl)
            else:
                client.set(key, value)
            logger.info(f"[Redis Cache SET] Key: {key}, TTL: {ttl}")
            return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}. Writing to in-memory fallback.")
            
    # Write to in-memory dictionary
    import time
    expiry = time.time() + ttl if ttl else None
    _memory_cache[key] = (value, expiry)
    logger.info(f"[InMemory Cache SET] Key: {key}, TTL: {ttl}")
    return True

def delete(key: str) -> bool:
    """ Deletes a key from Redis or local in-memory fallback. """
    client = _get_redis_client()
    deleted = False
    
    if client is not None:
        try:
            res = client.delete(key)
            deleted = res > 0
            logger.info(f"[Redis Cache DELETE] Key: {key}, Result: {deleted}")
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")
            
    if key in _memory_cache:
        del _memory_cache[key]
        deleted = True
        logger.info(f"[InMemory Cache DELETE] Key: {key}")
        
    return deleted

def expire(key: str, ttl: int) -> bool:
    """ Sets expiration TTL on a key. """
    client = _get_redis_client()
    if client is not None:
        try:
            return client.expire(key, ttl)
        except Exception as e:
            logger.warning(f"Redis expire failed: {e}")
            
    if key in _memory_cache:
        import time
        val, _ = _memory_cache[key]
        _memory_cache[key] = (val, time.time() + ttl)
        return True
    return False

# NAMESPACED KEY HELPERS
def get_property_key(property_id: Any) -> str:
    return f"property:listing:{property_id}"

def get_search_key(query: str) -> str:
    import hashlib
    h = hashlib.md5(query.encode("utf-8")).hexdigest()
    return f"property:search:{h}"

def get_onboarding_key(user_id: str) -> str:
    return f"onboarding:state:{user_id}"

def get_search_results_key(query_hash: str) -> str:
    return f"search:results:{query_hash}"

def get_autocomplete_key(prefix: str) -> str:
    return f"search:autocomplete:{prefix}"

def get_trending_key() -> str:
    return "search:trending"

def get_popular_property_key(property_id: Any) -> str:
    return f"search:popular:{property_id}"

def get_recommendation_key(user_id: str) -> str:
    return f"rec:user:{user_id}"

def get_similar_key(property_id: Any) -> str:
    return f"rec:similar:{property_id}"

def invalidate_search_cache():
    """ Wipes all keys matching the search pattern property:search:* """
    client = _get_redis_client()
    if client is not None:
        try:
            keys = client.keys("property:search:*")
            if keys:
                client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} property search cache entries.")
        except Exception as e:
            logger.warning(f"Failed to clear Redis search keys: {e}")
            
    # Clear in-memory fallback keys
    keys_to_del = [k for k in _memory_cache.keys() if k.startswith("property:search:")]
    for k in keys_to_del:
        del _memory_cache[k]


# DISTRIBUTED LOCKS (Symmetric locks)
def acquire_lock(lock_key: str, expire_seconds: int = 10) -> bool:
    """ Acquires a distributed lock using SETNX. """
    client = _get_redis_client()
    if client is not None:
        try:
            # set NX=True only sets if it doesn't exist
            res = client.set(f"lock:{lock_key}", "locked", ex=expire_seconds, nx=True)
            return res is True
        except Exception as e:
            logger.warning(f"Redis lock failed: {e}")
            
    # Local lock simulation
    lock_name = f"lock:{lock_key}"
    import time
    if lock_name in _memory_cache:
        val, expiry = _memory_cache[lock_name]
        if expiry > time.time():
            return False  # Already locked
            
    _memory_cache[lock_name] = ("locked", time.time() + expire_seconds)
    return True

def release_lock(lock_key: str) -> bool:
    """ Releases a distributed lock. """
    return delete(f"lock:{lock_key}")
