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
import pytest

from ecpy.testing.util import process_app_events, handle_dialog

with enaml.imports():
    from ecpy.instruments.widgets.profile_edition\
        import (SetValidator, ConnectionCreationDialog,
                ConnectionValidationWindow, SettingsCreationDialog,
                RenameSettingsPopup, ProfileEditionDialog)


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


def test_connection_creation_dialog(prof_plugin, model_infos,
                                    process_and_sleep):
    """Test the dialog dedicated to create new connections.

    """
    d = ConnectionCreationDialog(plugin=prof_plugin, model_infos=model_infos,
                                 existing=['false_connection2'])
    d.show()
    process_and_sleep()

    assert d.connection
    assert len(d._connections) == 2

    ws = d.central_widget().widgets()
    ws[0].selected_index = 1
    process_and_sleep()
    assert d.connection.declaration.id == 'false_connection3'


def test_connection_validation_window(prof_plugin, process_and_sleep,
                                      profile_infos):
    """Test the window used to check that connection infos allows to open a
    connection.

    """
    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    process_and_sleep()
    w = ConnectionValidationWindow(editor=ed.central_widget().widgets()[0])
    w.show()
    process_and_sleep()

    widgets = w.central_widget().widgets()
    p = widgets[-3]
    p.clicked = True
    assert 'The connection was successfully established' in widgets[-2].text

    widgets[-1].clicked = True
    process_app_events()


def test_settings_creation_dialog(prof_plugin, model_infos, process_and_sleep):
    """Test the dialog dedicated to create new settings.

    """
    d = SettingsCreationDialog(plugin=prof_plugin, model_infos=model_infos,
                               existing=['false_settings2'])
    d.show()
    process_and_sleep()

    assert d.settings
    assert len(d._settings) == 3

    ws = d.central_widget().widgets()
    ws[0].selected_index = 1
    process_and_sleep()

    ok = ws[-1]
    assert not ok.enabled

    n = ws[-3]
    n.text = 'dummy'
    assert ok.enabled

    n.validator.validate('false_settings2')
    assert not ok.enabled


def test_rename_settings_popup(prof_plugin, profile_infos, process_and_sleep):
    """Test the popup used to rename a settings.

    """
    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    process_and_sleep()

    ed_widgets = ed.central_widget().widgets()
    ed_widget = ed_widgets[0]

    nb = ed_widget.widgets()[5]
    nb.selected_tab = 'settings'
    process_and_sleep()
    c_page, s_page = nb.pages()

    # Open the renaming popup.
    s_page.page_widget().widgets()[3].clicked = True

    # Get the popup.
    assert len(RenameSettingsPopup.popup_views) == 1
    p = RenameSettingsPopup.popup_views[0]
    settings = p.settings
    ws = p.central_widget().widgets()
    ws[1].text = ''
    process_and_sleep()
    assert not ws[-1].enabled

    ws[1].text = ed_widget.settings[1].name
    ws[1].validator.validate(ed_widget.settings[1].name)
    assert not ws[-1].enabled

    ws[1].text = 'dummy'
    ws[1].validator.validate('dummy')
    process_and_sleep()
    assert ws[-1].enabled

    ws[-1].clicked = True
    process_and_sleep()

    assert settings.name == 'dummy'

    p = RenameSettingsPopup.popup_views[0]
    ws = p.central_widget().widgets()

    ws[1].text = 'dummy2'
    process_and_sleep()
    assert ws[-1].enabled

    ws[-2].clicked = True
    process_and_sleep()

    assert settings.name == 'dummy'


def test_profile_edition_dialog_ok(prof_plugin, process_and_sleep,
                                   profile_infos):
    """Test the dialog used to edit a profile.

    """
    profile_infos.connections.clear()
    profile_infos.settings.clear()

    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    process_and_sleep()

    ed_widgets = ed.central_widget().widgets()
    ed_widget = ed_widgets[0]

    nb = ed_widget.widgets()[5]
    c_page, s_page = nb.pages()

    # Add a connection
    with handle_dialog(cls=ConnectionCreationDialog):
        c_page.page_widget().widgets()[2].clicked = True

    process_and_sleep()

    # Add a settings
    with handle_dialog(cls=SettingsCreationDialog):
        s_page.page_widget().widgets()[2].clicked = True

    process_and_sleep()

    assert len(ed_widget.connections) == 1
    assert len(ed_widget.settings) == 1

    ed_widgets[-1].clicked = True
    process_app_events()

    assert len(profile_infos.connections) == 1
    assert len(profile_infos.settings) == 1


def test_profile_edition_dialog_cancel(prof_plugin, process_and_sleep,
                                       profile_infos):
    """Test the dialog used to edit a profile.

    """
    ed = ProfileEditionDialog(plugin=prof_plugin, profile_infos=profile_infos)
    ed.show()
    process_and_sleep()

    ed_widgets = ed.central_widget().widgets()
    ed_widget = ed_widgets[0]

    nb = ed_widget.widgets()[5]
    c_page, s_page = nb.pages()

    # Delete a connection and open valiadtion window
    c_page.page_widget().widgets()[3].clicked = True
    c_page.page_widget().widgets()[4].clicked = True

    # Delete a settings
    s_page.page_widget().widgets()[4].clicked = True

    process_and_sleep()
    w = ed_widget._validator

    assert len(ed_widget.connections) == 2
    assert len(ed_widget.settings) == 2

    ed_widgets[-2].clicked = True
    process_app_events()
    assert not ed.visible and not w.visible

    assert len(profile_infos.connections) == 3
    assert len(profile_infos.settings) == 3
