# -*- coding: utf-8 -*-

import anyjson
from .wrapper import CacheWrapper
from .utils import filter_kwargs, coerce_value


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

    @staticmethod
    def format_options(**options):
        if options.has_key('timeout'):
            options['time'] = int(options.pop('timeout', 0))
        if options.has_key('valtype'):
            options['type'] = options.pop('valtype', '')
        return options

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

    def is_exists(self, key, **kwargs):
        raise NotImplemented

    def expire(self, key, **kwargs):
        return

    def get_type_default(self, type = ''):
        return

    def load(self, key, **kwargs):
        if not self.is_exists(key, **kwargs):
            raise KeyError
        type = kwargs.get('type', '').lower()
        method = 'get_%s' % type
        if not type or not hasattr(self, method):
            method = 'get_data'
        try:
            self.before_get(key, type = type)
            prepared = getattr(self, method)(key, **kwargs)
            result = self.unprepare_value(prepared, type = type)
        except TypeError:
            result = self.get_type_default(type = type)
        if kwargs.get('touch'):
            self.expire(key, **kwargs)
        return result

    def save(self, key, value, **kwargs):
        type = kwargs.get('type', '').lower()
        method = 'put_%s' % type
        if not type or not hasattr(self, method):
            method = 'put_data'
        try:
            self.before_put(key, value, type = type)
            prepared = self.prepare_value(value, type = type)
            result = getattr(self, method)(key, prepared, **kwargs)
        except TypeError:
            prepared = self.prepare_value(None, type = type)
            result = self.put_data(key, prepared, **kwargs)
        self.expire(key, **kwargs)
        return result

    def before_get(self, key, type = ''):
        return

    def before_put(self, key, value, type = ''):
        return

    def get_data(self, key, **kwargs):
        return self.call_backend('get', key, **kwargs)

    def put_data(self, key, value, **kwargs):
        value = coerce_value(value)
        return self.call_backend('set', key, value, **kwargs)

    def call_backend(self, name, *args, **kwargs):
        """ Safe call method of the backend """
        method = getattr(self.backend, name)
        kwargs = filter_kwargs(method, **kwargs)
        return method(*args, **kwargs)
