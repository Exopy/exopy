# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the preferences plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import enaml
import pytest
from configobj import ConfigObj
from future.builtins import str
from enaml.workbench.api import Workbench

from ...util import (handle_dialog, ecpy_path)
from ...conftest import APP_DIR_CONFIG, APP_PREFERENCES

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from ecpy.app.app_manifest import AppManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.preferences.manifest import PreferencesManifest
    from .pref_utils import (PrefContributor, BadPrefContributor,
                             PrefContributor2)

PLUGIN_ID = 'ecpy.app.preferences'


class TestPreferencesPlugin(object):
    """Test the preferences plugin capabilities.

    """
    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(AppManifest())
        self.workbench.register(ErrorsManifest())

    def test_app_startup1(self, tmpdir, windows):
        """Test app start-up when no app_directory.ini exists.

        """
        manifest = PreferencesManifest()
        self.workbench.register(manifest)

        # Remove any trash app_directory.ini file. The global fixture ensure
        # that it cannot be a user file.
        app_pref = os.path.join(ecpy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
        if os.path.isfile(app_pref):
            os.remove(app_pref)

        # Start the app and fake a user answer.
        app = self.workbench.get_plugin('ecpy.app')

        app_dir = str(tmpdir.join('ecpy'))

        with handle_dialog(custom=lambda x: setattr(x, 'path', app_dir)):
            app.run_app_startup(object())

        assert os.path.isfile(app_pref)
        assert ConfigObj(app_pref)['app_path'] == app_dir
        assert os.path.isdir(app_dir)

    def test_app_startup2(self, tmpdir, windows):
        """Test app start-up when user quit app.

        """
        manifest = PreferencesManifest()
        self.workbench.register(manifest)

        # Remove any trash app_directory.ini file. The global fixture ensure
        # that it cannot be a user file.
        app_pref = os.path.join(ecpy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
        if os.path.isfile(app_pref):
            os.remove(app_pref)

        # Start the app and fake a user answer.
        app = self.workbench.get_plugin('ecpy.app')

        with pytest.raises(SystemExit):
            with handle_dialog('reject'):
                app.run_app_startup(object())

    def test_app_startup3(self, tmpdir, windows):
        """Test app start-up when a preference file already exists.

        """
        manifest = PreferencesManifest()
        self.workbench.register(manifest)

        # Create a trash app_directory.ini file. The global fixture ensure
        # that it cannot be a user file. Don't use app_dir fixture as I need to
        # test directory creation.
        app_pref = os.path.join(ecpy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
        app_dir = str(tmpdir.join('ecpy'))
        conf = ConfigObj()
        conf.filename = app_pref
        conf['app_path'] = app_dir
        conf.write()

        assert not os.path.isdir(app_dir)

        # Start the app and fake a user answer.
        app = self.workbench.get_plugin('ecpy.app')

        app.run_app_startup(object())

        assert os.path.isdir(app_dir)

    def test_lifecycle(self, app_dir):
        """Test the plugin lifecycle when no default.ini exist in app folder.

        """
        pref_man = PreferencesManifest()
        self.workbench.register(pref_man)
        c_man = PrefContributor()
        self.workbench.register(c_man)

        # Start preferences plugin.
        prefs = self.workbench.get_plugin(PLUGIN_ID)
        assert prefs.app_directory == app_dir
        assert os.path.isdir(os.path.join(app_dir, 'prefs'))
        core = self.workbench.get_plugin('enaml.workbench.core')
        assert core.invoke_command('ecpy.app.preferences.get',
                                   dict(plugin_id='test.prefs')) is not None

        self.workbench.register(PrefContributor2())
        assert core.invoke_command('ecpy.app.preferences.get',
                                   dict(plugin_id='test.prefs2')) is not None

        # Stopping
        self.workbench.unregister(c_man.id)
        with pytest.raises(KeyError):
            core.invoke_command('ecpy.app.preferences.get',
                                dict(plugin_id='test.prefs'))
        self.workbench.unregister(pref_man.id)
        assert not prefs._prefs
        assert not prefs._pref_decls

    def test_load_defaultini(self, app_dir):
        """Test that a default.ini file found in the app folder under prefs
        is loaded on startup.

        """
        prefs_path = os.path.join(app_dir, 'prefs')
        os.mkdir(os.path.join(app_dir, 'prefs'))

        conf = ConfigObj(os.path.join(prefs_path, 'default.ini'))
        c_man = PrefContributor()
        conf[c_man.id] = {}
        conf[c_man.id]['string'] = 'This is a test'
        conf.write()

        pref_man = PreferencesManifest()
        self.workbench.register(pref_man)
        self.workbench.register(c_man)

        c_pl = self.workbench.get_plugin(c_man.id)

        assert c_pl.string == 'This is a test'

    def test_update_contrib_and_type_checking(self, app_dir):
        """Check that the contributions are correctly updated when a new
        plugin is registered and check that the contribution is of the right
        type.

        """
        pref_man = PreferencesManifest()
        self.workbench.register(pref_man)
        c_man = PrefContributor()
        self.workbench.register(c_man)

        # Start preferences plugin.
        self.workbench.get_plugin(PLUGIN_ID)

        # Test observation of extension point and type checking.
        b_man = BadPrefContributor()
        with pytest.raises(TypeError):
            self.workbench.register(b_man)

    def test_auto_sync(self, app_dir):
        """Check that auito_sync members are correctly handled.

        """
        self.workbench.register(PreferencesManifest())
        c_man = PrefContributor()
        self.workbench.register(c_man)

        contrib = self.workbench.get_plugin(c_man.id)
        contrib.auto = 'test_auto'

        ref = {c_man.id: {'auto': 'test_auto'}}
        path = os.path.join(app_dir, 'prefs', 'default.ini')
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

        contrib.auto = 'test'

        ref = {c_man.id: {'auto': 'test'}}
        path = os.path.join(app_dir, 'prefs', 'default.ini')
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

    def test_save1(self, app_dir):
        """Test saving to the default file.

        """
        self.workbench.register(PreferencesManifest())
        c_man = PrefContributor()
        self.workbench.register(c_man)

        contrib = self.workbench.get_plugin(c_man.id)
        contrib.string = 'test_save'

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.save', {}, self)

        path = os.path.join(app_dir, 'prefs', 'default.ini')
        ref = {c_man.id: {'string': 'test_save', 'auto': ''}}
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

    def test_save2(self, app_dir):
        """Test saving to a specific file.

        """
        self.workbench.register(PreferencesManifest())
        c_man = PrefContributor()
        self.workbench.register(c_man)

        contrib = self.workbench.get_plugin(c_man.id)
        contrib.string = 'test_save'

        path = os.path.join(app_dir, 'prefs', 'custom.ini')
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.save', {'path': path})

        ref = {c_man.id: {'string': 'test_save', 'auto': ''}}
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

    def test_save3(self, app_dir, monkeypatch):
        """Test saving to a specific file.

        """
        self.workbench.register(PreferencesManifest())
        c_man = PrefContributor()
        self.workbench.register(c_man)

        contrib = self.workbench.get_plugin(c_man.id)
        contrib.string = 'test_save'

        prefs_path = os.path.join(app_dir, 'prefs')
        path = os.path.join(prefs_path, 'custom.ini')

        @classmethod
        def answer(*args, **kwargs):
            return path

        with enaml.imports():
            from ecpy.app.preferences.manifest import FileDialogEx
        monkeypatch.setattr(FileDialogEx, 'get_save_file_name', answer)
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.save', {'path': prefs_path,
                                                          'ask_user': True})

        ref = {c_man.id: {'string': 'test_save', 'auto': ''}}
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref
        assert self.workbench.get_plugin(PLUGIN_ID).last_directory == \
            prefs_path

    def test_load1(self, app_dir):
        """Test loading default preferences for unstarted plugin.

        """
        # Register and start preferences plugin
        self.workbench.register(PreferencesManifest())
        self.workbench.get_plugin(PLUGIN_ID)

        c_man = PrefContributor()
        self.workbench.register(c_man)

        path = os.path.join(app_dir, 'prefs', 'default.ini')
        conf = ConfigObj(path)
        conf[c_man.id] = {}
        conf[c_man.id]['string'] = 'test'
        conf.write()

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.load', {})
        assert self.workbench.get_plugin(c_man.id, False) is None
        contrib = self.workbench.get_plugin(c_man.id)

        assert contrib.string == 'test'

    def test_load2(self, app_dir):
        """Test loading preferences from non-existing file.

        """
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.load',
                            {'path': ''}, self)

        assert not self.workbench.get_plugin(PLUGIN_ID)._prefs

    def test_load3(self, app_dir):
        """Test loading preferences from non-default file for started plugin.

        """
        self.workbench.register(PreferencesManifest())
        c_man = PrefContributor()
        self.workbench.register(c_man)
        contrib = self.workbench.get_plugin(c_man.id)

        path = os.path.join(app_dir, 'prefs', 'custom.ini')
        conf = ConfigObj(path)
        conf[c_man.id] = {}
        conf[c_man.id]['string'] = 'test'
        conf.write()

        assert contrib.string == ''

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.load',
                            {'path': path}, self)

        assert contrib.string == 'test'

    def test_load4(self, app_dir, monkeypatch):
        """Test loading preferences from non-default file for started plugin.

        """
        self.workbench.register(PreferencesManifest())
        c_man = PrefContributor()
        self.workbench.register(c_man)
        contrib = self.workbench.get_plugin(c_man.id)

        prefs_path = os.path.join(app_dir, 'prefs')
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
            from ecpy.app.preferences.manifest import FileDialogEx
        monkeypatch.setattr(FileDialogEx, 'get_open_file_name', answer)
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.preferences.load',
                            {'path': prefs_path, 'ask_user': True}, self)

        assert contrib.string == 'test'
        assert self.workbench.get_plugin(PLUGIN_ID).last_directory == \
            prefs_path
