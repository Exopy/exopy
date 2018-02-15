# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the instrument model selection widget.

"""
import enaml

from exopy.testing.util import wait_for_window_displayed

with enaml.imports():
    from exopy.instruments.widgets.profile_selection\
        import (ProfileSelectionDialog)


def test_selecting_profile_from_scratch(prof_plugin, exopy_qtbot, dialog_sleep):
    """Test selecting a profile.

    """
    d = ProfileSelectionDialog(plugin=prof_plugin)
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    d.profile = 'fp2'
    assert not d.connection
    assert not d.settings
    exopy_qtbot.wait(10 + dialog_sleep)

    d.connection = 'false_connection1'
    d.settings = 'false_settings1'
    d.driver = 'instruments.test.FalseDriver%s' % ('' if d.driver.endswith('2')
                                                   else 2)
    assert not d.connection
    assert not d.settings
    exopy_qtbot.wait(10 + dialog_sleep)

    d.connection = 'false_connection'
    d.settings = 'false_settings'
    exopy_qtbot.wait(10 + dialog_sleep)

    d.central_widget().widgets()[-1].clicked = True

    def assert_result():
        assert d.result
    exopy_qtbot.wait_until(assert_result)


def test_editing_a_previous_selection(prof_plugin, exopy_qtbot, dialog_sleep):
    """Test editing a profile selection.

    """
    d = ProfileSelectionDialog(plugin=prof_plugin,
                               profile='fp2',
                               driver='instruments.test.FalseDriver2',
                               connection='false_connection',
                               settings='false_settings')
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    assert d.profile == 'fp2'
    assert d.driver == 'instruments.test.FalseDriver2'
    assert d.connection == 'false_connection'
    assert d.settings == 'false_settings'

    d.central_widget().widgets()[-2].clicked = True

    def assert_result():
        assert not d.result
    exopy_qtbot.wait_until(assert_result)


def test_using_custom_filtering(prof_plugin, exopy_qtbot, dialog_sleep):
    """Test using a custom filtering function to reduce the available profiles
    and drivers.

    """
    d = ProfileSelectionDialog(plugin=prof_plugin, profile='fp1',
                               filter_profiles=lambda p: ['fp1'],
                               filter_drivers=lambda d: [d[0]])
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    w = d.central_widget().widgets()[0]
    assert len(w._drivers) == 1
