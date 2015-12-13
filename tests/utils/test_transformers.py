# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test utility functions found in transformers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.utils.transformers import (basic_name_formatter, ids_to_unique_names)


def test_basic_name_formatter():
    """Test the base formatting.

    """
    assert basic_name_formatter('test_test') == 'Test test'


def test_ids_to_unique_names():
    """Test the ids to names conversion.

    """
    ids = ('ecpy.test.tester', 'ecpy.test.dummy_1', 'ecpy.dummy.dummy_1',
           'user.test.tester')
    assert (sorted(list(ids_to_unique_names(ids))) ==
            sorted(('test.Dummy 1', 'dummy.Dummy 1', 'ecpy.test.Tester',
                    'user.test.Tester')))
