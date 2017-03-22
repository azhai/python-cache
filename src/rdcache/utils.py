# -*- coding: utf-8 -*-

import inspect
import re
from datetime import date, datetime
from decimal import Decimal


def filter_kwargs(method, **kwargs):
    """ 只保留必须的关联参数 """
    args = inspect.getargspec(method).args
    return dict([(k, kwargs[k]) for k in args if k in kwargs])


def coerce_value(value):
    """ 将数据库字段类型转为简单类型 """
    if isinstance(value, datetime):
        value = value.strftime('%F %T')
    elif isinstance(value, date):
        value = value.strftime('%F')
    elif isinstance(value, Decimal):
        value = float(value)
    return value


def coerce_number(value, convert = float):
    """ 将数据库字段类型转为数值类型 """
    pattern = re.compile(r'^\d{4}(-\d\d){2}')
    format = '%Y-%m-%d %H:%M:%S'
    if isinstance(value, basestring) and pattern.match(value):
        #将字符串的日期时间先转为对象
        try:
            mask = format[:len(value) - 2]
            value = datetime.strptime(value, mask)
        except ValueError:
            pass
    if isinstance(value, date):
        value = value.strftime('%s')
    return convert(value)
