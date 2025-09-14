from datetime import timedelta
from django.core.cache import cache

class RedisRepository:
    def get(self, key):
        return cache.get(key=key)
    
    def set(self, key, value, timeout=timedelta(hours=1)):
        timeout_in_seconds = int(timeout.total_seconds())
        return cache.set(key=key, value=value, timeout=timeout_in_seconds)
    
    def delete(self, key):
        return cache.delete(key=key)
    
    def get_bulk(self, keys: list):
        return cache.get_many(keys=keys)

    def set_bulk(
        self, 
        keys: list, 
        values: list, 
        timeout=timedelta(hours=1)
        ):
        timeout_in_seconds = int(timeout.total_seconds())
        return cache.set_many(keys=keys, values=values, timeout=timeout_in_seconds)
    