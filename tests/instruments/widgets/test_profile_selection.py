# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the instrument model selection widget.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.instruments.widgets.profile_selection\
        import (ProfileSelectionDialog)


def test_selecting_profile_from_scratch(prof_plugin, process_and_sleep):
    """Test selecting a profile.

    """
    d = ProfileSelectionDialog(plugin=prof_plugin)
    d.show()
    process_and_sleep()

    d.profile = 'fp2'
    assert not d.connection
    assert not d.settings
    process_and_sleep()

    d.connection = 'false_connection1'
    d.settings = 'false_settings1'
    d.driver = 'tests.test.FalseDriver%s' % ('' if d.driver.endswith('2')
                                             else 2)
    assert not d.connection
    assert not d.settings
    process_and_sleep()

    d.connection = 'false_connection'
    d.settings = 'false_settings'
    process_and_sleep()

    d.central_widget().widgets()[-1].clicked = True
    process_app_events()
    assert d.result


def test_editing_a_previous_selection(prof_plugin, process_and_sleep):
    """Test editing a profile selection.

    """
    d = ProfileSelectionDialog(plugin=prof_plugin,
                               profile='fp2', driver='tests.test.FalseDriver2',
                               connection='false_connection',
                               settings='false_settings')
    d.show()
    process_and_sleep()

    assert d.profile == 'fp2'
    assert d.driver == 'tests.test.FalseDriver2'
    assert d.connection == 'false_connection'
    assert d.settings == 'false_settings'

    d.central_widget().widgets()[-2].clicked = True
    process_app_events()
    assert not d.result


def test_using_custom_filtering(prof_plugin, process_and_sleep):
    """Test using a custom filtering function to reduce the available profiles
    and drivers.

    """
    d = ProfileSelectionDialog(plugin=prof_plugin, profile='fp1',
                               filter_profiles=lambda p: ['fp1'],
                               filter_drivers=lambda d: [d[0]])
    d.show()
    process_and_sleep()

    w = d.central_widget().widgets()[0]
    assert len(w._drivers) == 1
