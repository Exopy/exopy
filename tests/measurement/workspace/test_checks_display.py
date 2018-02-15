# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test widgets related to measurement edition tasks.

"""
import enaml

from exopy.testing.util import handle_question, wait_for_window_displayed

with enaml.imports():
    from exopy.measurement.workspace.checks_display import ChecksDisplay


def test_checks_display_not_warning(exopy_qtbot, dialog_sleep):
    """Test displaying checks for a situation that do not allow enqueuing.

    """
    dial = ChecksDisplay(errors={'test': 'dummy', 'complex': {'rr': 'tt'}})

    dial.show()
    wait_for_window_displayed(exopy_qtbot, dial)
    exopy_qtbot.wait(dialog_sleep)

    assert dial.central_widget().widgets()[-1].text == 'Force enqueue'

    with handle_question(exopy_qtbot, 'no'):
        dial.central_widget().widgets()[-1].clicked = True

    def assert_result():
        assert not dial.result
    exopy_qtbot.wait_until(assert_result)


def test_checks_display_not_warning_force_enqueue(exopy_qtbot, dialog_sleep):
    """Test displaying checks for a situation that do not allow enqueuing.

    """
    dial = ChecksDisplay(errors={'test': 'dummy', 'complex': {'rr': 'tt'}})

    dial.show()
    wait_for_window_displayed(exopy_qtbot, dial)
    exopy_qtbot.wait(dialog_sleep)

    assert dial.central_widget().widgets()[-1].text == 'Force enqueue'

    with handle_question(exopy_qtbot, 'yes'):
        dial.central_widget().widgets()[-1].clicked = True

    def assert_result():
        assert dial.result
    exopy_qtbot.wait_until(assert_result)


def test_checks_display_warning(exopy_qtbot, dialog_sleep):
    """Test displaying checks that allow enqueuing.

    """
    dial = ChecksDisplay(errors={'test': 'dummy', 'internal': {'rr': 'tt'}},
                         is_warning=True)

    dial.show()
    wait_for_window_displayed(exopy_qtbot, dial)
    exopy_qtbot.wait(dialog_sleep)

    assert dial.central_widget().widgets()[-1].text == 'Enqueue'

    dial.central_widget().widgets()[-1].clicked = True

    def assert_result():
        assert dial.result
    exopy_qtbot.wait_until(assert_result)
