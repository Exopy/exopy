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
from collections import defaultdict


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


def flatten_config(config, entries):
    """ Gather entries from a configbj in sets.

    Parameters
    ----------
    config : Section
        Section from which the values of some entries should be extracted.

    entries : list(str)
        The list of entries to look for in the configobj.

    Returns
    -------
    results : dict(str: set)
        Dict containing the values of the entries as sets. This dict can then
        be used to gather function and or classes needed when rebuilding.

    """
    results = defaultdict(set)
    for entry in entries:
        # Make sure that all entries exists in the dict.
        results[entry]
        if entry in config.scalars:
            results[entry].add(config[entry])

    for section in config.sections:
        aux = flatten_config(config[section], entries)
        for key in aux:
            results[key].update(aux[key])

    return results
