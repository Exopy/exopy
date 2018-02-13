# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test widgets related to measure edition tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml

from exopy.testing.util import process_app_events, handle_question

with enaml.imports():
    from exopy.measure.workspace.checks_display import ChecksDisplay


def test_checks_display_not_warning(windows, dialog_sleep):
    """Test displaying checks for a situation that do not allow enqueuing.

    """
    dial = ChecksDisplay(errors={'test': 'dummy', 'complex': {'rr': 'tt'}})

    dial.show()
    process_app_events()
    sleep(dialog_sleep)

    assert dial.central_widget().widgets()[-1].text == 'Force enqueue'

    with handle_question('no'):
        dial.central_widget().widgets()[-1].clicked = True
    process_app_events()
    assert not dial.result


def test_checks_display_not_warning_force_enqueue(windows, dialog_sleep):
    """Test displaying checks for a situation that do not allow enqueuing.

    """
    dial = ChecksDisplay(errors={'test': 'dummy', 'complex': {'rr': 'tt'}})

    dial.show()
    process_app_events()
    sleep(dialog_sleep)

    assert dial.central_widget().widgets()[-1].text == 'Force enqueue'

    with handle_question('yes'):
        dial.central_widget().widgets()[-1].clicked = True
    process_app_events()
    assert dial.result


def test_checks_display_warning(windows, dialog_sleep):
    """Test displaying checks that allow enqueuing.

    """
    dial = ChecksDisplay(errors={'test': 'dummy', 'internal': {'rr': 'tt'}},
                         is_warning=True)

    dial.show()
    process_app_events()
    sleep(dialog_sleep)

    assert dial.central_widget().widgets()[-1].text == 'Enqueue'

    dial.central_widget().widgets()[-1].clicked = True
    process_app_events()

    assert dial.result
