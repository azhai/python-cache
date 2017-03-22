# cache: caching for humans

## Installation

    pip install rdcache

## Usage:

``` python
# For memcache
import pylibmc
from rdcache import Cache
backend = pylibmc.Client(["127.0.0.1"])
cache = Cache(backend)

# For Redis
REDIS_CONFS = {
    "default": {
        "host": "127.0.0.1",
        "port": 6379,
        "password": "",
        "db": 0,
    },
}
from rdcache.ext import RedisCache, RedisPool
redis = RedisPool(REDIS_CONFS)
cache = RedisCache(redis.get('default'), touch = True)


@cache("mykey")
def some_expensive_method():
    sleep(10)
    return 42

# writes 42 to the cache
some_expensive_method()

# reads 42 from the cache
some_expensive_method()

# re-calculates and writes 42 to the cache
some_expensive_method.refresh()

# get the cached value or throw an error
# (unless default= was passed to @cache(...))
some_expensive_method.cached()
```

## Options

Options can be passed to either the `Cache` constructor or the decorator.  Options passed to the decorator take precedence.  Available options are:

    enabled    If `False`, the backend cache will not be used at all,
               and your functions will be run as-is, even when you call
               `.cached()`.  This is useful for development, when the
               function may be changing rapidly.
               Default: True

    default    If given, `.cached()` will return the given value instead
               of raising a KeyError.
               
    type       data/json
               hash/list/set/zset (if backend is redis)
               Default: data
               
    time       expire seconds
               Default: -1 (forever)
                
    touch      If true, expire time seconds everytime include reading data 


The remaining options, if given, will be passed as keyword arguments to the backend's `set` method.  This is useful for things like expiration times - for example, using pylibmc:

``` python
@cache("some_key_%s_%d", type='json', time=3600)
def expensive_method(name, ver=1):
    # ...
```

## Dummy Cache

Cache provides a "fake" caches for local development without a backend cache: `DummyCache`.

### P.S.

If you're a Ruby user, check out the analogous [Cacher][] library for Ruby

[Cacher]: https://github.com/jayferd/cacher
