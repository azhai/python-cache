import sys
from os.path import join, dirname

from setuptools import setup, find_packages
sys.path.insert(0, join(dirname(__file__), 'src'))
from rdcache import __version__
sys.path.pop(0)

setup(
    name="rdcache",
    version=__version__,
    description="caching for humans, forked from jneen/python-cache",
    author="Jay Adkisson, Ryan Liu",
    author_email="azhai (at) 126 (dot) com",
    url="https://github.com/azhai/rdcache",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Topic :: Database :: Front-Ends",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=["cache", "decorator"],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['redis', 'anyjson'], #if use rdcache.ext.RedisCache
)
