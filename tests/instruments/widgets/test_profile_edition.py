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
import pytest

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.instruments.widgets.profile_edition\
        import (SetValidator, ConnectionCreationDialog,
                ConnectionValidationWindow, SettingsCreationDialog,
                RenameSettingsPopup, ProfileEditionDialog)


@pytest.fixture
def process_and_sleep(windows, dialog_sleep):
    """Function to process app events and sleep.

    """
    def p():
        process_app_events()
        sleep(dialog_sleep)

    return p


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


def test_rename_settings_popup(prof_plugin):
    """Test the popup used to rename a settings.

    """
    pass


def test_profile_edition_dialog(prof_plugin):
    """Test the dialog used to edit a profile.

    """
    pass
