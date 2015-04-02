# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility function to work with nested list of dictionaries.

That kind of structure is often generated when walking a hierarchical ensemble
of objects such as Tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
from collections import defaultdict


def flatten_walk(walk, entries):
    """ Convert a nested list in a flat dict by gathering entries in sets.

    Parameters
    ----------
    walk : list
        The nested list returned by the walk method of the root task.

    entries : list(str)
        The list of entries to look for in the walk.

    Returns
    -------
    results : dict(str: set)
        Dict containing the values of the entries as sets. This dict can then
        be used to gather function and or classes needed at runtime.

    """
    results = defaultdict(set)
    for step in walk:
        if isinstance(step, list):
            aux = flatten_walk(step, entries)
            for key in aux:
                results[key].update(aux[key])
        else:
            for entry in entries:
                if entry in step and step[entry] is not None:
                    results[entry].add(step[entry])

    return results
