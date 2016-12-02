# -*- coding: utf-8 -*-

import redis
import anyjson
from datetime import date, datetime
from decimal import Decimal
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
    
    special_types = ['hashes']
    
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
        
    def is_empty(self, value, **kwargs):
        result = super(RedisCache, self).is_empty(value, **kwargs)
        if result is False:
            type = kwargs.pop('type', '')
            if type in self.special_types:
                result = not value
        return result

    def prepare_value(self, value, **kwargs):
        value = super(RedisCache, self).prepare_value(value, **kwargs)
        value = self.coerce_string(value)
        return anyjson.dumps(value)

    def unprepare_value(self, prepared, **kwargs):
        prepared = super(RedisCache, self).unprepare_value(prepared, **kwargs)
        return anyjson.loads(prepared)

    def get_hashes(self, key, **kwargs):
        return self.backend.hgetall(key)

    def set_hashes(self, key, value, **kwargs):
        if not value:
            return
        for k, v in value.items():
            value[k] = self.coerce_string(v)
        result = self.backend.hmset(key, value)
        return result