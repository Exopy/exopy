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

from time import sleep

import enaml

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.instruments.widgets.instrument_selection\
        import ModelSelectionDialog
    from ..contributors import InstrContributor1


def test_model_selection_widget(windows, instr_workbench, dialog_sleep):
    """Test the capabilities of the model selection widget.

    """
    def process():
        process_app_events()
        sleep(dialog_sleep)

    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')

    h = p._manufacturers

    d = ModelSelectionDialog(plugin=p)
    sel = d.central_widget().widgets()[0]
    tr = sel.widgets()[-1]
    d.show()
    process()

    tr.auto_expand = True
    sel.kind = 'Lock-in'
    process()
    assert len(h.manufacturers) == 1

    sel.kind = 'All'

    tr.selected_item = h._manufacturers['Dummy']
    process()

    assert len(h._manufacturers['Dummy'].instruments) == 2
    sel.use_series = False
    process()
    assert h.use_series == sel.use_series
    assert len(h._manufacturers['Dummy'].instruments) == 3

    sel.use_series = True

    tr.selected_item = h._manufacturers['Dummy']._series['dumb']
    process()

    tr.selected_item = h._manufacturers['Dummy']._models['001']
    process()
    assert d.model

    d.close()
