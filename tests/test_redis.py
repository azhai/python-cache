# -*- coding: utf-8 -*-

import unittest
from datetime import date
from rdcache.ext import RedisCache, RedisPool

redis = RedisPool({
    "default": {
        "host": "127.0.0.1",
        "port": 6379,
        "password": "",
        "db": 0,
    },
})
backend = redis.get('default')
cache = RedisCache(backend, touch = True)


user_rows = {
    'alice': {'username':'alice',   'gender':'F',   'birthday':date(1981,10,10)},
    'bob':   {'username':'bob',     'gender':'M',   'birthday':date(1988,9,9)},
    'candy': {'username':'candy',   'gender':'F',   'birthday':date(1983,7,15)},
    'david': {'username':'david',   'gender':'M',   'birthday':date(1992,1,3)},
    'emily': {'username':'eric',    'gender':'M',   'birthday':date(1991,12,25)},
}

@cache('user:%s', type = 'hash', time = 60)
def read_user(username):
    return user_rows.get(username)

@cache('birthes', type = 'zset', time = 120)
def read_birthes():
    return [(u, user_rows[u]['birthday']) for u in user_rows.iterkeys()]

def get_user(username):
    user = read_user(username)
    key = 'user:%s' % username
    if backend.type(key) == 'hash':
        user2 = backend.hgetall(key)
    else:
        user2 = {}
    return user, user2

def get_birthes():
    birthes = dict(read_birthes())
    birthes2 = dict(backend.zrange('birthes',
                    0, -1, withscores = True))
    return birthes, birthes2


class RedisCacheTestCase(unittest.TestCase):
    """ 单元测试 """

    def test_none(self):
        eric, eric2 = get_user('eric')
        self.assertEqual(eric, {})
        self.assertEqual(eric2, {})

    def test_hash(self):
        candy, candy2 = get_user('candy')
        self.assertEqual(candy, candy2)

    def test_zset(self):
        birthes, birthes2 = get_birthes()
        self.assertEqual(len(birthes), len(birthes2))
        for k, v in birthes.iteritems():
            self.assertEqual(v, birthes2.get(k))


if __name__ == '__main__':
    unittest.main()