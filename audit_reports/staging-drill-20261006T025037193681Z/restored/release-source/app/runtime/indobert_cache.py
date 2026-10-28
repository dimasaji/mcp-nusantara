import threading

_LOCK = threading.RLock()
_CACHE = {}

def get_cached(cls, *args, **kwargs):
    key = (
        cls.__module__,
        cls.__name__,
        repr(args),
        repr(sorted((k, str(v)) for k, v in kwargs.items()))
    )
    with _LOCK:
        if key not in _CACHE:
            _CACHE[key] = cls.from_pretrained(*args, **kwargs)
        return _CACHE[key]

def cache_stats():
    with _LOCK:
        return {
            "cached_objects": len(_CACHE),
            "keys": [f"{k[0]}.{k[1]}" for k in _CACHE]
        }

def clear_cache():
    with _LOCK:
        _CACHE.clear()
