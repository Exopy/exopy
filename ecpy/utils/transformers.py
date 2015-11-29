# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility functions to perform string transformations.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collections import defaultdict, OrderedDict


def basic_name_formatter(name):
    """Basic formmater turning '_' in ' ' and capitalising.

    """
    return name.replace('_', ' ').capitalize()


def ids_to_unique_names(ids, name_formatter=basic_name_formatter,
                        separator='.'):
    """Make the easiest to read names from ids without duplicate.

    Parameters
    ----------
    ids : iterable[unicode]
        Iterable of ids from which to build the names.

    name_formatter : callable, optional
        Callable making a name more human readdable. It is applied only to
        the last part of the id (after last separator occurence).

    separator : unicode, optional
        Character used as separator between the different parts of an id.

    Returns
    -------
    names : dict
        Dictionary mapping the unique names to their original ids.

    """
    mapping = {i: i.split(separator) for i in ids}
    valid_names = defaultdict(list)
    for i, parts in mapping.items():
        valid_names[name_formatter(parts[-1])].append(i)

    while any(len(v) > 1 for v in valid_names.values()):
        for name in list(valid_names):
            ids = valid_names[name]
            if len(ids) > 1:
                del valid_names[name]
                for i in ids:
                    new_name = (mapping[i][-len(name.split(separator))-1] +
                                separator + name)
                    valid_names[new_name].append(i)

    names = {v[0]: k for k, v in valid_names.items()}
    return OrderedDict(((names[i], i) for i in ids))
