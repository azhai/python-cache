# -*- coding: utf-8 -*-

import inspect
from .wrapper import CacheWrapper


def filter_kwargs(method, **kwargs):
    """ Just leave the needed kwargs """
    args = inspect.getargspec(method).args
    return dict([(k, kwargs[k]) for k in args if k in kwargs])


class Cache(object):
    """
    Creates a cache decorator factory.

        cache = Cache(a_cache_client)

    Positional Arguments:
    backend    This is a cache backend that must have "set" and "get"
               methods defined on it.  This would typically be an
               instance of, for example, `pylibmc.Client`.

    Keyword Arguments:
    enabled    If `False`, the backend cache will not be used at all,
               and your functions will be run as-is, even when you call
               `.cached()`.  This is useful for development, when the
               function may be changing rapidly.
               Default: True
    """
    
    _CACHE_NONE = '###CACHE_NONE###'
    special_types = []

    def __init__(self, backend = None, enabled = True, **default_options):
        self.backend, self.enabled = backend, enabled
        self.default_options = default_options

    def __call__(self, key = None, **kwargs):
        """
        Returns the decorator itself
            @cache("mykey", ...)
            def expensive_method():
                # ...

            # or in the absence of decorators

            expensive_method = cache("mykey", ...)(expensive_method)

        Positional Arguments:

        key    (string) The key to set

        Keyword Arguments:

        The decorator takes the same keyword arguments as the Cache
        constructor.  Options passed to this method supercede options
        passed to the constructor.

        """

        options = self.default_options.copy()
        options.update(kwargs)
        options = self.format_options(**options)

        def _cache(fn):
            cache_key = key or 'cache:%s' % fn.__name__
            return CacheWrapper(self, cache_key, fn, **options)

        return _cache
        
    def format_options(self, **options):
        if options.has_key('timeout'):
            options['time'] = int(options.pop('timeout', 0))
        if options.has_key('valtype'):
            options['type'] = options.pop('valtype', '')
        return options
        
    def call_backend(self, name, *args, **kwargs):
        """ Safe call method of the backend """
        method = getattr(self.backend, name)
        kwargs = filter_kwargs(method, **kwargs)
        return method(*args, **kwargs)

    def prepare_key(self, key, *args, **kwargs):
        """ Generate cache key """
        if args:
            return key % args
        else:
            return key % kwargs

    def prepare_value(self, value, **kwargs):
        """ encode value """
        if value is None:
            return self._CACHE_NONE
        else:
            return value

    def unprepare_value(self, prepared, **kwargs):
        """ decode value """
        if prepared is self._CACHE_NONE:
            return None
        else:
            return prepared
        
    def expire(self, key, **kwargs):
        return
        
    def is_empty(self, value, **kwargs):
        #Need a None or empty struct to raise KeyError
        #e.g. redis.hgetall() return empty dict
        return value in [None, self._CACHE_NONE]

    def get_value(self, key, **kwargs):
        prepared = self.call_backend('get', key, **kwargs)
        return self.unprepare_value(prepared, **kwargs)

    def set_value(self, key, value, **kwargs):
        prepared = self.prepare_value(value, **kwargs)
        return self.call_backend('set', key, prepared, **kwargs)

    def get(self, key, **kwargs):
        type = kwargs.get('type', '').lower()
        if type in self.special_types:
            method = 'get_%s' % type
        else:
            method = 'get_value'
        value = getattr(self, method)(key, **kwargs)
        if self.is_empty(value, **kwargs):
            raise KeyError
        if kwargs.get('touch'):
            self.expire(key, **kwargs)
        return value

    def set(self, key, value, **kwargs):
        type = kwargs.get('type', '').lower()
        if type in self.special_types:
            method = 'set_%s' % type
        else:
            method = 'set_value'
        result = getattr(self, method)(key, value, **kwargs)
        self.expire(key, **kwargs)
        return result
