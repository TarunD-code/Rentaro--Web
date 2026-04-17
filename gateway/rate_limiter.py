import time
from collections import defaultdict

# In-memory dictionary to track rate limiting per IP as an alternative to Redis
# since docker/redis were not found on this Windows system.
RATE_LIMITS = defaultdict(list)

# Max 500 requests per minute
MAX_REQUESTS = 500
WINDOW_SECONDS = 60

def check_rate_limit(client_ip: str) -> bool:
    """
    Check if a client IP has exceeded the allowed number of requests in a given window.
    Returns True if allowed, False if rejected (rate limited)
    """
    if not client_ip:
        return True
        
    current_time = time.time()
    
    # Filter out old requests
    RATE_LIMITS[client_ip] = [
        timestamp for timestamp in RATE_LIMITS[client_ip] 
        if current_time - timestamp < WINDOW_SECONDS
    ]
    
    # Check limit
    if len(RATE_LIMITS[client_ip]) >= MAX_REQUESTS:
        return False
        
    # Record new request
    RATE_LIMITS[client_ip].append(current_time)
    return True
