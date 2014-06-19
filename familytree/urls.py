"""
URL Helpers
-----------

- :func:`append` - append path segments to a URL

This module exists to simplify URL manipulation on top of the
standard library.

"""

import urllib.parse


def append(root, *segments):
    """
    Safely append ``segments`` to ``root``.

    :param root: the URI stem to start with
    :param segments: path segments to append in order
    :return: the new URI

    """
    if root.endswith('/'):
        root = root[:-1]
    return '{0}/{1}'.format(
        root,
        '/'.join(urllib.parse.quote(segment.strip('/'))
                 for segment in segments),
    )
