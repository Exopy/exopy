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
import pytest

from exopy.testing.util import handle_dialog, wait_for_window_displayed

with enaml.imports():
    from exopy.instruments.widgets.profile_edition\
        import (SetValidator, ConnectionCreationDialog,
                ConnectionValidationWindow, SettingsCreationDialog,
                RenameSettingsPopup, ProfileEditionDialog,
                clean_name, trim_description)


# HINT the QtListStrWidget has some issues of display in test mode


@pytest.fixture
def profile_infos(prof_plugin):
    """A profile model to edit.

    """
    return prof_plugin._profiles['fp1']


@pytest.fixture
def model_infos(profile_infos):
    """A model infos to use for testing.

    """
    return profile_infos.model


def test_set_validator():
    """Test the SetValidator used to restrict allowed names.

    """
    v = SetValidator(existing=['a', 'b', 'c'])
    assert not v.validate('a') and not v.valid
    assert v.validate('bc') and v.valid


def test_clean_name():
    """Test cleaning a name.

    """
    assert clean_name('a_b') == 'a b'


def test_trim_description():
    """Test triming the description (connection or settings).

    """
    desc = """test\n\nDefaults\n-------\n\n details"""
    assert trim_description(desc) == 'test'


def test_connection_creation_dialog(prof_plugin, model_infos, exopy_qtbot,
                                    dialog_sleep):
    """Test the dialog dedicated to create new connections.

    """
    d = ConnectionCreationDialog(plugin=prof_plugin, model_infos=model_infos,
                                 existing=['false_connection2'])
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    assert d.connection
    assert len(d._connections) == 2

    ws = d.central_widget().widgets()
    ws[0].selected_item = ws[0].items[1]

    def assert_id():
        assert d.connection.declaration.id == 'false_connection3'
    exopy_qtbot.wait_until(assert_id)
    ws[-1].clicked = True  # Ok button

    def assert_result():
        assert d.result
    exopy_qtbot.wait_until(assert_result)
    exopy_qtbot.wait(dialog_sleep)

    d = ConnectionCreationDialog(plugin=prof_plugin, model_infos=model_infos,
                                 existing=['false_connection2'])
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    d.central_widget().widgets()[-2].clicked = True  # Cancel button

    def assert_result():
        assert not d.result
    exopy_qtbot.wait_until(assert_result)
    exopy_qtbot.wait(dialog_sleep)


def test_connection_validation_window(prof_plugin, exopy_qtbot, dialog_sleep,
                                      profile_infos):
    """Test the window used to check that connection infos allows to open a
    connection.

    """
    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    wait_for_window_displayed(exopy_qtbot, ed)
    exopy_qtbot.wait(dialog_sleep)

    w = ConnectionValidationWindow(editor=ed.central_widget().widgets()[0])
    w.show()
    wait_for_window_displayed(exopy_qtbot, w)
    exopy_qtbot.wait(dialog_sleep)

    widgets = w.central_widget().widgets()
    form_widgets = widgets[0].widgets()
    combo_driver = form_widgets[1]
    combo_connection = form_widgets[3]
    combo_settings = form_widgets[5]

    combo_driver.selected = 'test <instruments.test.FalseDriver2>'
    combo_connection.selected = 'false_connection2'
    combo_settings.selected = 'false_settings2'

    p = widgets[-3]
    p.clicked = True
    assert 'The connection was successfully established' in widgets[-2].text

    # XXX add a test for failed connection test

    widgets[-1].clicked = True
    exopy_qtbot.wait(10)


def test_settings_creation_dialog(prof_plugin, model_infos, exopy_qtbot,
                                  dialog_sleep):
    """Test the dialog dedicated to create new settings.

    """
    d = SettingsCreationDialog(plugin=prof_plugin, model_infos=model_infos,
                               existing=['false_settings2'])
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    assert d.settings
    assert len(d._settings) == 3

    ws = d.central_widget().widgets()
    ws[0].selected_item = ws[0].items[1]
    ok = ws[-1]

    def assert_enabled():
        assert not ok.enabled
    exopy_qtbot.wait_until(assert_enabled)
    exopy_qtbot.wait(dialog_sleep)

    n = ws[-3]
    n.text = 'dummy'
    assert ok.enabled

    n.validator.validate('false_settings2')
    assert not ok.enabled

    n = ws[-3]
    n.text = 'dummy'
    ok.clicked = True
    assert d.settings.user_id == n.text
    assert d.result

    d2 = SettingsCreationDialog(plugin=prof_plugin, model_infos=model_infos,
                                existing=['false_settings2'])
    d2.show()
    wait_for_window_displayed(exopy_qtbot, d2)
    d2.central_widget().widgets()[-2].clicked = False  # Cancel button

    def assert_result():
        assert not d2.result
    exopy_qtbot.wait_until(assert_result)


def test_rename_settings_popup(prof_plugin, profile_infos, exopy_qtbot,
                               dialog_sleep):
    """Test the popup used to rename a settings.

    """
    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    wait_for_window_displayed(exopy_qtbot, ed)
    exopy_qtbot.wait(dialog_sleep)

    ed_widgets = ed.central_widget().widgets()
    ed_widget = ed_widgets[0]

    nb = ed_widget.widgets()[5]
    nb.selected_tab = 'settings'
    exopy_qtbot.wait(10 + dialog_sleep)
    c_page, s_page = nb.pages()

    # Open the renaming popup.
    s_page.page_widget().widgets()[3].clicked = True

    # Get the popup.
    assert len(RenameSettingsPopup.popup_views) == 1
    p = RenameSettingsPopup.popup_views[0]
    settings = p.settings
    ws = p.central_widget().widgets()
    ws[1].text = ''

    def assert_enabled():
        assert not ws[-1].enabled
    exopy_qtbot.wait_until(assert_enabled)
    exopy_qtbot.wait(dialog_sleep)

    ws[1].text = ed_widget.settings[1].name
    ws[1].validator.validate(ed_widget.settings[1].name)
    assert not ws[-1].enabled

    ws[1].text = 'dummy'
    ws[1].validator.validate('dummy')

    def assert_enabled():
        assert ws[-1].enabled
    exopy_qtbot.wait_until(assert_enabled)
    exopy_qtbot.wait(dialog_sleep)

    ws[-1].clicked = True

    def assert_user_id():
        assert settings.user_id == 'dummy'
    exopy_qtbot.wait_until(assert_user_id)
    exopy_qtbot.wait(dialog_sleep)

    exopy_qtbot.wait_until(lambda: len(RenameSettingsPopup.popup_views) == 0)

    # Open a new popup and cancel the name change
    s_page.page_widget().widgets()[3].clicked = True

    assert len(RenameSettingsPopup.popup_views) == 1
    p = RenameSettingsPopup.popup_views[0]
    ws = p.central_widget().widgets()

    ws[1].text = 'dummy2'

    def assert_enabled():
        assert ws[-1].enabled
    exopy_qtbot.wait_until(assert_enabled)
    exopy_qtbot.wait(dialog_sleep)

    ws[-2].clicked = True

    def assert_user_id():
        assert settings.user_id == 'dummy'
    exopy_qtbot.wait_until(assert_user_id)
    exopy_qtbot.wait(dialog_sleep)


def test_profile_edition_dialog_ok(prof_plugin, dialog_sleep, exopy_qtbot,
                                   profile_infos):
    """Test the dialog used to edit a profile.

    """
    # XXX need to test model selection
    profile_infos.connections.clear()
    profile_infos.settings.clear()

    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    wait_for_window_displayed(exopy_qtbot, ed)
    exopy_qtbot.wait(dialog_sleep)

    ed_widgets = ed.central_widget().widgets()
    ed_widget = ed_widgets[0]

    nb = ed_widget.widgets()[5]
    c_page, s_page = nb.pages()

    # Add a connection
    with handle_dialog(exopy_qtbot, cls=ConnectionCreationDialog):
        c_page.page_widget().widgets()[2].clicked = True

    exopy_qtbot.wait(10 + dialog_sleep)

    # Add a settings
    with handle_dialog(exopy_qtbot, cls=SettingsCreationDialog):
        s_page.page_widget().widgets()[2].clicked = True

    exopy_qtbot.wait(10 + dialog_sleep)

    assert len(ed_widget.connections) == 1
    assert len(ed_widget.settings) == 1

    ed_widgets[-1].clicked = True

    def assert_cn_st():
        assert len(profile_infos.connections) == 1
        assert len(profile_infos.settings) == 1
    exopy_qtbot.wait_until(assert_cn_st)


def test_profile_edition_dialog_cancel(prof_plugin, exopy_qtbot, dialog_sleep,
                                       profile_infos):
    """Test the dialog used to edit a profile.

    """
    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    wait_for_window_displayed(exopy_qtbot, ed)
    exopy_qtbot.wait(dialog_sleep)

    ed_widgets = ed.central_widget().widgets()
    ed_widget = ed_widgets[0]

    nb = ed_widget.widgets()[5]
    c_page, s_page = nb.pages()

    # Delete a connection and open valiadtion window
    c_page.page_widget().widgets()[3].clicked = True
    c_page.page_widget().widgets()[4].clicked = True

    # Delete a settings
    s_page.page_widget().widgets()[4].clicked = True

    exopy_qtbot.wait(10 + dialog_sleep)
    w = ed_widget._validator

    assert len(ed_widget.connections) == 2
    assert len(ed_widget.settings) == 2

    ed_widgets[-2].clicked = True

    def assert_visible():
        assert not ed.visible and not w.visible
    exopy_qtbot.wait_until(assert_visible)

    assert len(profile_infos.connections) == 3
    assert len(profile_infos.settings) == 3
