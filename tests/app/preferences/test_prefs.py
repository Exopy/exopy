# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the preferences plugin.

"""
import os
import enaml
import pytest
from configobj import ConfigObj
from future.builtins import str

from exopy.testing.util import (handle_dialog, exopy_path, APP_DIR_CONFIG,
                                APP_PREFERENCES)

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from exopy.app.app_manifest import AppManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from .pref_utils import (PrefContributor, BadPrefContributor,
                             PrefContributor2)

PLUGIN_ID = 'exopy.app.preferences'


@pytest.fixture
def pref_workbench(workbench):
    """Register the plugins resuired to test the preferences plugin.

    """
    workbench.register(CoreManifest())
    workbench.register(AppManifest())
    workbench.register(ErrorsManifest())
    return workbench


def test_app_startup1(pref_workbench, tmpdir, exopy_qtbot):
    """Test app start-up when no app_directory.ini exists.

    """
    manifest = PreferencesManifest()
    pref_workbench.register(manifest)

    # Remove any trash app_directory.ini file. The global fixture ensure
    # that it cannot be a user file.
    app_pref = os.path.join(exopy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
    if os.path.isfile(app_pref):
        os.remove(app_pref)

    # Start the app and fake a user answer.
    app = pref_workbench.get_plugin('exopy.app')

    app_dir = str(tmpdir.join('exopy'))

    with handle_dialog(exopy_qtbot,
                       handler=lambda bot, d: setattr(d, 'path', app_dir)):
        app.run_app_startup(object())

    assert os.path.isfile(app_pref)
    assert ConfigObj(app_pref)['app_path'] == app_dir
    assert os.path.isdir(app_dir)


def test_app_startup2(pref_workbench, tmpdir, exopy_qtbot):
    """Test app start-up when user quit app.

        """
        manifest = PreferencesManifest()
        self.workbench.register(manifest)

        # Remove any trash app_directory.ini file. The global fixture ensure
        # that it cannot be a user file.
        app_pref = os.path.join(exopy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
        if os.path.isfile(app_pref):
            os.remove(app_pref)

        # Start the app and fake a user answer.
        app = self.workbench.get_plugin('exopy.app')

    with pytest.raises(SystemExit):
        with handle_dialog(exopy_qtbot, 'reject'):
            app.run_app_startup(object())


def test_app_startup3(pref_workbench, tmpdir, exopy_qtbot):
    """Test app start-up when a preference file already exists.

    """
    manifest = PreferencesManifest()
    pref_workbench.register(manifest)

    # Create a trash app_directory.ini file. The global fixture ensure
    # that it cannot be a user file. Don't use app_dir fixture as I need to
    # test directory creation.
    app_pref = os.path.join(exopy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
    app_dir = str(tmpdir.join('exopy'))
    conf = ConfigObj(encoding='utf8')
    conf.filename = app_pref
    conf['app_path'] = app_dir
    conf.write()

    assert not os.path.isdir(app_dir)

    # Start the app and fake a user answer.
    app = pref_workbench.get_plugin('exopy.app')

    app.run_app_startup(object())

    assert os.path.isdir(app_dir)


def test_app_startup4(pref_workbench, tmpdir, exopy_qtbot):
    """Test app start-up when user request to reset app folder.

    """
    manifest = PreferencesManifest()
    pref_workbench.register(manifest)

    app_dir = str(tmpdir.join('exopy'))

    # Add a app_directory.ini file.
    app_pref = os.path.join(exopy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
    if not os.path.isfile(app_pref):
        conf = ConfigObj(encoding='utf8')
        conf.filename = app_pref
        conf['app_path'] = app_dir
        conf.write()

    # Start the app and fake a user answer.
    app = pref_workbench.get_plugin('exopy.app')

    class DummyArgs(object):

        reset_app_folder = True

    with handle_dialog(exopy_qtbot,
                       handler=lambda bot, x: setattr(x, 'path', app_dir)):
        app.run_app_startup(DummyArgs)

    assert os.path.isfile(app_pref)
    assert ConfigObj(app_pref)['app_path'] == app_dir
    assert os.path.isdir(app_dir)


def test_lifecycle(pref_workbench, app_dir):
    """Test the plugin lifecycle when no default.ini exist in app folder.

    """
    pref_man = PreferencesManifest()
    pref_workbench.register(pref_man)
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    # Start preferences plugin.
    prefs = pref_workbench.get_plugin(PLUGIN_ID)
    assert prefs.app_directory == app_dir
    assert os.path.isdir(os.path.join(app_dir, 'preferences'))
    core = pref_workbench.get_plugin('enaml.workbench.core')
    assert core.invoke_command('exopy.app.preferences.get',
                               dict(plugin_id='test.prefs')) is not None

    pref_workbench.register(PrefContributor2())
    assert core.invoke_command('exopy.app.preferences.get',
                               dict(plugin_id='test.prefs2')) is not None

    # Stopping
    pref_workbench.unregister(c_man.id)
    with pytest.raises(KeyError):
        core.invoke_command('exopy.app.preferences.get',
                            dict(plugin_id='test.prefs'))
    pref_workbench.unregister(pref_man.id)
    assert not prefs._prefs
    assert not prefs._pref_decls


def test_load_defaultini(pref_workbench, app_dir):
    """Test that a default.ini file found in the app folder under prefs
    is loaded on startup.

    """
    prefs_path = os.path.join(app_dir, 'preferences')
    os.mkdir(os.path.join(app_dir, 'preferences'))

    conf = ConfigObj(os.path.join(prefs_path, 'default.ini'))
    c_man = PrefContributor()
    conf[c_man.id] = {}
    conf[c_man.id]['string'] = 'This is a test'
    conf.write()

    pref_man = PreferencesManifest()
    pref_workbench.register(pref_man)
    pref_workbench.register(c_man)

    c_pl = pref_workbench.get_plugin(c_man.id)

    assert c_pl.string == 'This is a test'


def test_update_contrib_and_type_checking(pref_workbench, app_dir):
    """Check that the contributions are correctly updated when a new
    plugin is registered and check that the contribution is of the right
    type.

    """
    pref_man = PreferencesManifest()
    pref_workbench.register(pref_man)
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    # Start preferences plugin.
    pref_workbench.get_plugin(PLUGIN_ID)

    # Test observation of extension point and type checking.
    b_man = BadPrefContributor()
    with pytest.raises(TypeError):
        pref_workbench.register(b_man)


def test_auto_sync(pref_workbench, app_dir):
    """Check that auito_sync members are correctly handled.

    """
    pref_workbench.register(PreferencesManifest())
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.auto = 'test_auto'

    ref = {c_man.id: {'auto': 'test_auto'}}
    path = os.path.join(app_dir, 'preferences', 'default.ini')
    assert os.path.isfile(path)
    assert ConfigObj(path).dict() == ref

    contrib.auto = 'test'

    ref = {c_man.id: {'auto': 'test'}}
    path = os.path.join(app_dir, 'preferences', 'default.ini')
    assert os.path.isfile(path)
    assert ConfigObj(path).dict() == ref


def test_save1(pref_workbench, app_dir):
    """Test saving to the default file.

    """
    pref_workbench.register(PreferencesManifest())
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.string = 'test_save'

    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.save', {}, pref_workbench)

    path = os.path.join(app_dir, 'preferences', 'default.ini')
    ref = {c_man.id: {'string': 'test_save', 'auto': ''}}
    assert os.path.isfile(path)
    assert ConfigObj(path).dict() == ref


def test_save2(pref_workbench, app_dir):
    """Test saving to a specific file.

    """
    pref_workbench.register(PreferencesManifest())
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.string = 'test_save'

    path = os.path.join(app_dir, 'preferences', 'custom.ini')
    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.save', {'path': path})

    ref = {c_man.id: {'string': 'test_save', 'auto': ''}}
    assert os.path.isfile(path)
    assert ConfigObj(path).dict() == ref


def test_save3(pref_workbench, app_dir, monkeypatch):
    """Test saving to a specific file.

    """
    pref_workbench.register(PreferencesManifest())
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.string = 'test_save'

    prefs_path = os.path.join(app_dir, 'preferences')
    path = os.path.join(prefs_path, 'custom.ini')

    @classmethod
    def answer(*args, **kwargs):
        return path

    with enaml.imports():
        from exopy.app.preferences.manifest import FileDialogEx
    monkeypatch.setattr(FileDialogEx, 'get_save_file_name', answer)
    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.save', {'path': prefs_path,
                                                      'ask_user': True})

    ref = {c_man.id: {'string': 'test_save', 'auto': ''}}
    assert os.path.isfile(path)
    assert ConfigObj(path).dict() == ref
    assert pref_workbench.get_plugin(PLUGIN_ID).last_directory == \
        prefs_path


def test_load1(pref_workbench, app_dir):
    """Test loading default preferences for unstarted plugin.

    """
    # Register and start preferences plugin
    pref_workbench.register(PreferencesManifest())
    pref_workbench.get_plugin(PLUGIN_ID)

    c_man = PrefContributor()
    pref_workbench.register(c_man)

    path = os.path.join(app_dir, 'preferences', 'default.ini')
    conf = ConfigObj(path)
    conf[c_man.id] = {}
    conf[c_man.id]['string'] = 'test'
    conf.write()

    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.load', {})
    assert pref_workbench.get_plugin(c_man.id, False) is None
    contrib = pref_workbench.get_plugin(c_man.id)

    assert contrib.string == 'test'


def test_load2(pref_workbench, app_dir):
    """Test loading preferences from non-existing file.

    """
    pref_workbench.register(PreferencesManifest())
    pref_workbench.register(PrefContributor())

    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.load',
                        {'path': ''}, pref_workbench)

    assert not pref_workbench.get_plugin(PLUGIN_ID)._prefs


def test_load3(pref_workbench, app_dir):
    """Test loading preferences from non-default file for started plugin.

    """
    pref_workbench.register(PreferencesManifest())
    c_man = PrefContributor()
    pref_workbench.register(c_man)
    contrib = pref_workbench.get_plugin(c_man.id)

    path = os.path.join(app_dir, 'preferences', 'custom.ini')
    conf = ConfigObj(path)
    conf[c_man.id] = {}
    conf[c_man.id]['string'] = 'test'
    conf.write()

    assert contrib.string == ''

    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.load',
                        {'path': path}, pref_workbench)

    assert contrib.string == 'test'


def test_load4(pref_workbench, app_dir, monkeypatch):
    """Test loading preferences from non-default file for started plugin.

    """
    pref_workbench.register(PreferencesManifest())
    c_man = PrefContributor()
    pref_workbench.register(c_man)
    contrib = pref_workbench.get_plugin(c_man.id)

    prefs_path = os.path.join(app_dir, 'preferences')
    path = os.path.join(prefs_path, 'custom.ini')
    conf = ConfigObj(path)
    conf[c_man.id] = {}
    conf[c_man.id]['string'] = 'test'
    conf.write()

    assert contrib.string == ''

    @classmethod
    def answer(*args, **kwargs):
        return path

    with enaml.imports():
        from exopy.app.preferences.manifest import FileDialogEx
    monkeypatch.setattr(FileDialogEx, 'get_open_file_name', answer)
    core = pref_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.preferences.load',
                        {'path': prefs_path, 'ask_user': True}, pref_workbench)

    assert contrib.string == 'test'
    assert pref_workbench.get_plugin(PLUGIN_ID).last_directory == \
        prefs_path


# =============================================================================
# --- API import --------------------------------------------------------------
# =============================================================================

def test_api_import():
    """Test importing the api module.

    """
    from exopy.app.preferences import api
    assert api.__all__
