# distributedlock settings
import distributedlock
from django.core.cache import get_cache


distributedlock.DEFAULT_TIMEOUT = 60 * 5
distributedlock.DEFAULT_MEMCACHED_CLIENT = get_cache('default')

# import after distributedlock settings
from distributedlock import distributedlock, LockNotAcquiredError
