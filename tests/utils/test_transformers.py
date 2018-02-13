# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test utility functions found in transformers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from exopy.utils.transformers import (basic_name_formatter,
                                      ids_to_unique_names)


def test_basic_name_formatter():
    """Test the base formatting.

    """
    assert basic_name_formatter('test_test') == 'Test test'


def test_ids_to_unique_names():
    """Test the ids to names conversion.

    """
    ids = ('exopy.test.tester', 'exopy.test.dummy_1', 'exopy.dummy.dummy_1',
           'user.test.tester')
    assert (sorted(list(ids_to_unique_names(ids))) ==
            sorted(('test.Dummy 1', 'dummy.Dummy 1', 'exopy.test.Tester',
                    'user.test.Tester')))


def test_ids_to_unique_names2():
    """Test the ids to names conversion with preformatting.

    """
    ids = ('exopy.test.tester', 'exopy.test.dummy_1', 'exopy.dummy.dummy_1',
           'user.test.tester')
    names = ids_to_unique_names(ids, preformatter=lambda x: x.capitalize())
    assert (sorted(names) ==
            sorted(('test.Dummy 1', 'dummy.Dummy 1', 'Exopy.test.Tester',
                    'User.test.Tester')))
    assert names['User.test.Tester'] == ids[-1]


def test_ids_to_unique_names3():
    """Test the ids to names conversion.

    """
    ids = ('exopy.test.tester', 'exopy.test.dummy_1', 'exopy.dummy.dummy_1',
           'user.test.tester')
    assert (sorted(list(ids_to_unique_names(ids, reverse=True))) ==
            sorted(ids))
