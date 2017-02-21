# -*- coding: utf-8 -*-

from datetime import date, datetime
from decimal import Decimal

import redis

from .cache import Cache


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
        
    def coerce_string(self, value):
        if isinstance(value, datetime):
            value = value.strftime('%F %T')
        elif isinstance(value, date):
            value = value.strftime('%F')
        elif isinstance(value, Decimal):
            value = float(value)
        return value
    
    def expire(self, key, **kwargs):
        if kwargs.has_key('time'):
            time = int(kwargs['time'])
            return self.backend.expire(key, time)

    def is_exists(self, key, **kwargs):
        return self.backend.exists(key)

    def get_data(self, key, **kwargs):
        val_type = self.backend.type(key)
        if val_type != 'string':
            raise TypeError
        return self.call_backend('get', key, **kwargs)

    def put_data(self, key, value, **kwargs):
        value = self.coerce_string(value)
        return self.call_backend('set', key, value, **kwargs)

    def get_hash(self, key, **kwargs):
        return self.backend.hgetall(key)

    def put_hash(self, key, value, **kwargs):
        if not value:
            return 0
        for k, v in value.items():
            value[k] = self.coerce_string(v)
        result = self.backend.hmset(key, value)
        return result

    def get_list(self, key, **kwargs):
        return self.backend.lrange(key, 0, -1)

    def put_list(self, key, value, **kwargs):
        self.backend.ltrim(key, 1, 0)  # 清空
        for v in value:
            v = self.coerce_string(v)
            self.backend.rpush(key, v)
        return self.backend.llen(key)

    def get_set(self, key, **kwargs):
        return self.backend.sunion(key)

    def put_set(self, key, value, **kwargs):
        value = self.coerce_string(value)
        result = self.backend.sadd(key, value)
        return result

    def get_sorted(self, key, **kwargs):
        withscores = kwargs.pop('withscores', False)
        return self.backend.zrangebyscore(key, '-inf', '+inf',
                                        withscores=withscores)

    def put_sorted(self, key, value, **kwargs):
        score = float(kwargs.get('score', 0.0))
        value = self.coerce_string(value)
        return self.backend.zadd(key, score, value)
