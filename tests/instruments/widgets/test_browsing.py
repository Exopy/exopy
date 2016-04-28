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

import os
from time import sleep

import enaml
from enaml.widgets.api import Container
from configobj import ConfigObj

from ecpy.testing.util import process_app_events, handle_dialog

with enaml.imports():
    from ecpy.instruments.widgets.browsing import BrowsingDialog
    from ecpy.instruments.widgets.profile_edition import ProfileEditionDialog


def test_browsing_dialog_instruments(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to explore the instruments.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    d.show()
    process_and_sleep()

    sel = nb.pages()[0].page_widget().widgets()[0]
    sel.use_series = False
    process_app_events()
    sel.model = prof_plugin._manufacturers.manufacturers[0].instruments[0]
    process_and_sleep()

    assert type(nb.pages()[0].page_widget().widgets()[1]) is not Container


def test_browing_dialog_profiles_add(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    process_and_sleep()

    btn = nb.pages()[1].page_widget().widgets()[-2]

    origin = prof_plugin.profiles[:]
    with handle_dialog('reject', cls=ProfileEditionDialog):
        btn.clicked = True

    assert prof_plugin.profiles == origin

    def handle(dial):
        assert dial.creation
        dial.profile_infos.id = 'test'
        dial.profile_infos.model = prof_plugin._profiles['fp1'].model

    with handle_dialog('accept', handle, cls=ProfileEditionDialog):
        btn.clicked = True

    # Wait for file notification to be treated
    sleep(1.0)
    process_app_events()

    assert 'test' in prof_plugin.profiles
    assert os.path.isfile(os.path.join(prof_plugin._profiles_folders[0],
                                       'test.instr.ini'))


def test_browing_dialog_profiles_edit(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    process_and_sleep()

    c = nb.pages()[1].page_widget()
    btn = c.widgets()[-1]
    c.p_id = 'fp1'

    manu = prof_plugin._manufacturers._manufacturers['Dummy']
    model = manu._series['dumb']._models['002']

    def handle(dial):
        dial.profile_infos.model = model

    with handle_dialog('reject', handle, cls=ProfileEditionDialog):
        btn.clicked = True

    assert prof_plugin._profiles['fp1'].model != model

    def handle(dial):
        assert not dial.creation
        dial.profile_infos.model = model
        dial.central_widget().widgets()[0].sync()

    with handle_dialog('accept', handle, cls=ProfileEditionDialog):
        btn.clicked = True

    assert prof_plugin._profiles['fp1'].model == model
    assert (ConfigObj(prof_plugin._profiles['fp1'].path)['model_id'] ==
            'Dummy.dumb.002')


def test_browing_dialog_profiles_use(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to follow the use of profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profile_use'
    d.show()
    process_and_sleep()

    f = nb.pages()[-1].page_widget().widgets()[0].scroll_widget()
    assert len(f.widgets()) == 2
    p, m = prof_plugin.get_profiles('tests2', ['fp1', 'fp2'])
    assert len(p) == 2
    process_and_sleep()
    print(f.children[-1].iterable)
    assert len(f.widgets()) == 6
    prof_plugin.release_profiles('tests2', ['fp2'])
    process_and_sleep()
    assert len(f.widgets()) == 4
