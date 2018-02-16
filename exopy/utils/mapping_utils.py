# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Mapping related utility functions.

"""
from collections import Mapping


def recursive_update(to_update, data):
    """Update a dictionary and all the mapping found as values.

    Parameters
    ----------
    to_update : Mapping
        Mapping whose content should be updated.

    data : Mapping
        Mapping to use from which to pull new values.

    """
    for k, v in data.items():
        if isinstance(v, Mapping):
            if k not in to_update:
                to_update[k] = {}
            recursive_update(to_update[k], v)
        else:
            to_update[k] = v
