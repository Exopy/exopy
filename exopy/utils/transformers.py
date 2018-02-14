# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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
                        separator='.', preformatter=None, reverse=False):
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

    preformatter : callable, optional
        Preformat ids before looking for shorter names.

    reverse : bool, optional
        If False the mapping returned map the names to the ids, otherwise it
        maps the ids to the names.

    Returns
    -------
    names : dict
        Dictionary mapping the unique names to their original ids.

    """
    if preformatter:
        ids_mapping = {preformatter(i): i for i in ids}
        ids = list(ids_mapping)

    mapping = {i: i.split(separator) for i in ids}
    valid_names = defaultdict(list)
    for i, parts in mapping.items():
        valid_names[name_formatter(parts[-1])].append(i)

    while any(len(v) > 1 for v in valid_names.values()):
        for name in list(valid_names):
            non_uniques = valid_names[name]
            if len(non_uniques) > 1:
                del valid_names[name]
                for i in non_uniques:
                    new_name = (mapping[i][-len(name.split(separator))-1] +
                                separator + name)
                    valid_names[new_name].append(i)

    names = {v[0]: k for k, v in valid_names.items()}

    if preformatter:
        mapping = OrderedDict(((names[i], ids_mapping[i]) for i in ids))
    else:
        mapping = OrderedDict(((names[i], i) for i in ids))

    if reverse:
        mapping = OrderedDict((v, k) for k, v in mapping.items())

    return mapping
