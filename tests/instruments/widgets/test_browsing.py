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
import os

import enaml
from enaml.widgets.api import Container
from configobj import ConfigObj

from exopy.testing.util import handle_dialog, wait_for_window_displayed

with enaml.imports():
    from enaml.stdlib.message_box import MessageBox
    from exopy.instruments.widgets.browsing import BrowsingDialog
    from exopy.instruments.widgets.profile_edition import ProfileEditionDialog


def test_browsing_dialog_instruments(exopy_qtbot, prof_plugin, dialog_sleep):
    """Test the browsing dialog page dedicated to explore the instruments.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    sel = nb.pages()[2].page_widget().widgets()[0]
    sel.use_series = False
    exopy_qtbot.wait(10)
    sel.model = prof_plugin._manufacturers.manufacturers[0].instruments[0]
    exopy_qtbot.wait(10 + dialog_sleep)

    def assert_widget():
        assert type(nb.pages()[0].page_widget().widgets()[1]) is not Container
    exopy_qtbot.wait_until(assert_widget)


def test_browing_dialog_profiles_add(exopy_qtbot, prof_plugin, dialog_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    btn = nb.pages()[0].page_widget().widgets()[-3]

    origin = prof_plugin.profiles[:]
    with handle_dialog(exopy_qtbot, 'reject', cls=ProfileEditionDialog):
        btn.clicked = True

    assert prof_plugin.profiles == origin

    def handle(bot, dial):
        assert dial.creation
        dial.profile_infos.id = 'test'
        dial.profile_infos.model = prof_plugin._profiles['fp1'].model

    with handle_dialog(exopy_qtbot, 'accept', handle,
                       cls=ProfileEditionDialog):
        btn.clicked = True

    # Wait for file notification to be treated
    exopy_qtbot.wait(1000)

    def assert_profiles():
        assert 'test' in prof_plugin.profiles
        assert os.path.isfile(os.path.join(prof_plugin._profiles_folders[0],
                                           'test.instr.ini'))
    exopy_qtbot.wait_until(assert_profiles)


def test_browing_dialog_profiles_edit(exopy_qtbot, prof_plugin, dialog_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    c = nb.pages()[0].page_widget()
    btn = c.widgets()[-2]
    c.p_id = 'fp1'

    manu = prof_plugin._manufacturers._manufacturers['Dummy']
    model = manu._series['dumb']._models['002']

    def handle(bot, dial):
        dial.profile_infos.model = model

    with handle_dialog(exopy_qtbot, 'reject', handle,
                       cls=ProfileEditionDialog):
        btn.clicked = True

    assert prof_plugin._profiles['fp1'].model != model

    def handle(bot, dial):
        assert not dial.creation
        dial.profile_infos.model = model
        dial.central_widget().widgets()[0].sync()

    with handle_dialog(exopy_qtbot, 'accept', handle,
                       cls=ProfileEditionDialog):
        btn.clicked = True

    assert prof_plugin._profiles['fp1'].model == model
    assert (ConfigObj(prof_plugin._profiles['fp1'].path)['model_id'] ==
            'Dummy.dumb.002')


def test_browing_dialog_profiles_delete(exopy_qtbot, prof_plugin,
                                        dialog_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    c = nb.pages()[0].page_widget()
    btn = c.widgets()[-1]
    c.p_id = 'fp1'
    print(prof_plugin._profiles)

    with handle_dialog(exopy_qtbot, 'reject', cls=MessageBox):
        btn.clicked = True

    assert 'fp1' in prof_plugin._profiles

    def handle(bot, dial):
        dial.buttons[0].was_clicked = True

    with handle_dialog(exopy_qtbot, 'accept', handle, cls=MessageBox):
        btn.clicked = True

    exopy_qtbot.wait(1000)

    def assert_profiles():
        assert 'fp1' not in prof_plugin._profiles
    exopy_qtbot.wait_until(assert_profiles)


def test_browsing_dialog_profiles_use(prof_plugin, exopy_qtbot, dialog_sleep):
    """Test the browsing dialog page dedicated to follow the use of profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profile_use'
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    f = nb.pages()[1].page_widget().widgets()[0].scroll_widget()
    assert len(f.widgets()) == 2
    p, m = prof_plugin.get_profiles('tests2', ['fp1', 'fp2'])
    assert len(p) == 2

    # Debug print
    print(f.children[-1].iterable)

    def assert_children():
        assert len(f.widgets()) == 6
    exopy_qtbot.wait_until(assert_children)
    exopy_qtbot.wait(dialog_sleep)

    prof_plugin.release_profiles('tests2', ['fp2'])

    def assert_children():
        assert len(f.widgets()) == 4
    exopy_qtbot.wait_until(assert_children)
    exopy_qtbot.wait(dialog_sleep)
