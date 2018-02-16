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
    from exopy.instruments.widgets.instrument_selection\
        import ModelSelectionDialog
    from ..contributors import InstrContributor1


def test_model_selection_widget(exopy_qtbot, instr_workbench, dialog_sleep):
    """Test the capabilities of the model selection widget.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('exopy.instruments')

    h = p._manufacturers

    d = ModelSelectionDialog(plugin=p)
    sel = d.central_widget().widgets()[0]
    tr = sel.widgets()[-1]
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    tr.auto_expand = True
    sel.kind = 'Lock-in'

    def assert_manufacturers():
        assert len(h.manufacturers) == 1
    exopy_qtbot.wait_until(assert_manufacturers)
    exopy_qtbot.wait(dialog_sleep)

    sel.kind = 'All'
    tr.selected_item = h._manufacturers['Dummy']

    def assert_manufacturers():
        assert len(h._manufacturers['Dummy'].instruments) == 2
    exopy_qtbot.wait_until(assert_manufacturers)
    exopy_qtbot.wait(dialog_sleep)

    sel.use_series = False

    def assert_use_series():
        assert h.use_series == sel.use_series
    exopy_qtbot.wait_until(assert_use_series)
    exopy_qtbot.wait(dialog_sleep)
    assert len(h._manufacturers['Dummy'].instruments) == 3

    sel.use_series = True

    tr.selected_item = h._manufacturers['Dummy']._series['dumb']
    exopy_qtbot.wait(100)
    exopy_qtbot.wait(dialog_sleep)

    tr.selected_item = h._manufacturers['Dummy']._models['001']
    exopy_qtbot.wait(100)
    exopy_qtbot.wait(dialog_sleep)

    d.central_widget().widgets()[-1].clicked = True

    def assert_model():
        assert d.instr_model
    exopy_qtbot.wait_until(assert_model)
    exopy_qtbot.wait(dialog_sleep)
