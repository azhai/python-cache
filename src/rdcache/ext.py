# -*- coding: utf-8 -*-

import redis
from .cache import Cache
from .utils import coerce_value, coerce_number


class RedisPool:
    """ Redis connection registry """
    
    registry = {}
    
    def __init__(self, configs):
        self.configs = configs
        
    def __contains__(self, current):
        return current in self.registry
    
    def connect(self, name):
        conf = self.configs.get(name, {})
        conf['host'] = conf.get('host', '127.0.0.1')
        conf['port'] = int(conf.get('port', 6379))
        conf['password'] = conf.get('password', '')
        conf['db'] = int(conf.get('db', 0))
        pool = redis.ConnectionPool(**conf)
        return redis.StrictRedis(connection_pool = pool)
        
    def get(self, current = 'default'):
        conn = self.__class__.registry.get(current)
        if not conn:
            conn = self.connect(current)
            self.__class__.registry[current] = conn
        return conn


class RedisCache(Cache):
    """ Redis cache """
    
    def __init__(self, backend, **default_options):
        enabled = default_options.pop('enabled', True)
        super(RedisCache, self).__init__(backend, enabled, **default_options)

    def is_exists(self, key, **kwargs):
        return self.backend.exists(key)

    def expire(self, key, **kwargs):
        if kwargs.has_key('time'):
            time = int(kwargs['time'])
            return self.backend.expire(key, time)

    def get_type_default(self, type = ''):
        if type == 'hash':
            return {}
        elif type == 'list' or type == 'zset':
            return []
        elif type == 'set':
            return set()

    def before_get(self, key, type = ''):
        if type == 'json':
            type = 'string'
        if self.backend.type(key) != type: #没有缓存
            raise TypeError
        return

    def before_put(self, key, value, type = ''):
        self.backend.delete(key)
        if type not in ['string', 'json']:
            if not value:
                raise TypeError
        return

    def get_hash(self, key, **kwargs):
        return self.backend.hgetall(key)

    def put_hash(self, key, value, **kwargs):
        for k, v in value.iteritems():
            value[k] = coerce_value(v)
        result = self.backend.hmset(key, value)
        return result

    def get_zset(self, key, **kwargs):
        withscores = kwargs.pop('withscores', True)
        return self.backend.zrangebyscore(key, '-inf', '+inf',
                                        withscores=withscores)

    def put_zset(self, key, value, **kwargs):
        items = {}
        if isinstance(value, dict):
            value = value.items()
        for k, v in value:
            items[k] = coerce_number(v)
        return self.backend.zadd(key, **items)

    def get_list(self, key, **kwargs):
        return self.backend.lrange(key, 0, -1)

    def put_list(self, key, value, **kwargs):
        value = [coerce_value(v) for v in value]
        return self.backend.rpush(key, *value)

    def get_set(self, key, **kwargs):
        return self.backend.sunion(key)

    def put_set(self, key, value, **kwargs):
        value = [coerce_value(v) for v in value]
        return self.backend.sadd(key, *value)
