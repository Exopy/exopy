# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility function to work with ConfigObj objects.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
from configobj import Section


def include_configobj(new_parent, config):
    """ Make a ConfigObj part of another one and preserves the depth.

    This function will copy all entries from config.

    Parameters
    ----------
    new_parent : configobj.Section
        Section in which information should be added.

    config : configobj.Section
        Section to merge into the new_parent.

    """
    for key, val in config.iteritems():
        if isinstance(val, Section):
            new_parent[key] = {}
            include_configobj(new_parent[key], val)

        else:
            new_parent[key] = val


def traverse_config(config, depth=-1):
    """Traverse a ConfigObj object by yielding all sections.

    Parameters
    ----------
    depth : int
        How deep should we explore the tree of tasks. When this number
        reaches zero deeper children should not be explored but simply
        yielded.

    """
    yield config

    if depth == 0:
        for s in config.sections:
            yield config[s]

    else:
        for s in config.sections:
            for c in traverse_config(config[s], depth - 1):
                yield c
