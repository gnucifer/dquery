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

# The following is modeled after the ISC license.
__copyright__ = """\
        2012 David Gustafsson <david.gustafsson@xelera.se>

        Permission to use, copy, modify, and distribute this software for any
        purpose with or without fee is hereby granted, provided that the above
        copyright notice and this permission notice appear in all copies.

        THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
        WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
        MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
        ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
        WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
        ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
        OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
        """

__todo__ = """\
    * TODO
"""

"""__all__ = [
    os.path.splitext(os.path.basename(handler))[0]
        for path in __path__
        for handler in os.listdir(path) if fnmatch(handler, 'dquer*.py')]
"""
