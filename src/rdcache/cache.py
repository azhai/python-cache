# -*- coding: utf-8 -*-

import inspect
import anyjson

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

    def prepare_value(self, value, type = ''):
        """ encode value """
        if type == 'json':
            return anyjson.dumps(value)
        elif value is None:
            return self._CACHE_NONE
        else:
            return value

    def unprepare_value(self, prepared, type = ''):
        """ decode value """
        if type == 'json':
            return anyjson.loads(prepared)
        elif prepared == self._CACHE_NONE:
            return None
        else:
            return prepared

    def is_empty(self, value):
        return value == self._CACHE_NONE or not value

    def load(self, key, **kwargs):
        #Need a None or empty struct to raise KeyError
        #e.g. redis.hgetall() return empty dict
        if not self.is_exists(key, **kwargs):
            raise KeyError
        result = self.get(key, **kwargs)
        if kwargs.get('touch'):
            self.expire(key, **kwargs)
        return result

    def save(self, key, value, **kwargs):
        result = self.put(key, value, **kwargs)
        self.expire(key, **kwargs)
        return result

    def get(self, key, **kwargs):
        type = kwargs.get('type', '').lower()
        self.before_get(key, type = type)
        if kwargs.get('fill_none'):
            try:
                value = self.get_data(key, **kwargs)
                if self.is_empty(value):
                    return None
            except TypeError:
                pass
        method = 'get_%s' % type
        if not type or not hasattr(self, method):
            method = 'get_data'
        prepared = getattr(self, method)(key, **kwargs)
        return self.unprepare_value(prepared, type = type)

    def put(self, key, value, **kwargs):
        type = kwargs.get('type', '').lower()
        self.before_put(key, type = type)
        if kwargs.get('fill_none'):
            if self.is_empty(value):
                prepared = self.prepare_value(None)
                return self.put_data(key, prepared, **kwargs)
        method = 'put_%s' % type
        if not type or not hasattr(self, method):
            method = 'put_data'
        prepared = self.prepare_value(value, type = type)
        return getattr(self, method)(key, prepared, **kwargs)

    def before_get(self, key, type = ''):
        return

    def before_put(self, key, type = ''):
        return

    def expire(self, key, **kwargs):
        return

    def is_exists(self, key, **kwargs):
        raise NotImplemented

    def get_data(self, key, **kwargs):
        return self.call_backend('get', key, **kwargs)

    def put_data(self, key, value, **kwargs):
        return self.call_backend('set', key, value, **kwargs)
