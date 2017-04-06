# -*- coding: utf-8 -*-

__version__ = "1.1.5"

from .wrapper import CacheWrapper
from .cache import Cache
from .dummy import DummyBackend
from .ext import RedisCache, RedisPool
from .utils import filter_kwargs, coerce_value, coerce_number

