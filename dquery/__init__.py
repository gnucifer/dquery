import os
from fnmatch import fnmatch

__project__ = "dquery"
__version__ = "dev"
__package__ = "dquery"
__description__ = "Drupal query tool inspired by gentoo's equery"
__author__ = "David Gustafsson"
__author_email__ = "david.gustafsson@xelera.se"
__url__ = "http://todo.com"

__classifiers__ = [
    "Programming Language :: Python :: 2.4",
    "Programming Language :: Python :: 2.5",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Topic :: System :: Systems Administration",
    "Environment :: Console",
    "Development Status :: 3 - Alpha"
]

__keywords__ = "drupal command line administration tool"


__requires__ = [] #TODO: what to put here?

"""__all__ = [
    os.path.splitext(os.path.basename(handler))[0]
        for path in __path__
        for handler in os.listdir(path) if fnmatch(handler, 'dquer*.py')]
"""
