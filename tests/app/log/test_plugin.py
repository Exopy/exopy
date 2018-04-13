# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the log plugin.

"""
import os
import sys
import logging
from enaml.workbench.api import Workbench
from exopy.testing.util import handle_dialog
import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from exopy.app.app_manifest import AppManifest
    from exopy.app.states.manifest import StateManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from exopy.app.log.manifest import LogManifest

from exopy.app.log.tools import (LogModel, GuiHandler, StreamToLogRedirector)


PLUGIN_ID = 'exopy.app.logging'


class CMDArgs(object):
    pass


class TestLogPlugin(object):
    """Test all the commands deined by the LogPLugin.

    """
    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(AppManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(LogManifest())

    def teardown(self):
        self.workbench.unregister(PLUGIN_ID)

    def test_handler1(self, logger):
        """Test adding removing handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        handler = GuiHandler(model=LogModel())
        core.invoke_command('exopy.app.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)
        log_plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert log_plugin.handler_ids == ['ui']
        assert handler in logger.handlers
        assert log_plugin._handlers == {'ui': (handler, 'test')}

        core.invoke_command('exopy.app.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert log_plugin.handler_ids == []
        assert handler not in logger.handlers
        assert log_plugin._handlers == {}

    def test_handler2(self, logger):
        """Test adding a GUI handler using the mode keyword.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command('exopy.app.logging.add_handler',
                            {'id': 'ui', 'mode': 'ui', 'logger': 'test'},
                            self)
        log_plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert log_plugin.handler_ids == [u'ui']
        assert logger.handlers

        core.invoke_command('exopy.app.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert log_plugin.handler_ids == []
        assert not logger.handlers

    def test_handler3(self, logger):
        """Test adding an handler using a non recognised mode.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command('exopy.app.logging.add_handler',
                            {'id': 'ui', 'logger': 'test'},
                            self)
        log_plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert log_plugin.handler_ids == []
        assert not logger.handlers

    def test_filter1(self, logger):
        """Test adding removing filter.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        handler = GuiHandler(model=LogModel())
        core.invoke_command('exopy.app.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)

        class Filter(object):

            def filter(self, record):
                return True

        test_filter = Filter()

        core.invoke_command('exopy.app.logging.add_filter',
                            {'id': 'filter', 'filter': test_filter,
                             'handler_id': 'ui'},
                            self)

        log_plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert log_plugin.filter_ids == [u'filter']
        assert log_plugin._filters == {u'filter': (test_filter, u'ui')}

        core.invoke_command('exopy.app.logging.remove_filter',
                            {'id': 'filter'}, self)

        assert log_plugin.filter_ids == []
        assert log_plugin._filters == {}

    def test_filter2(self):
        """Test adding a filter and removing the handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        handler = GuiHandler(model=LogModel())
        core.invoke_command('exopy.app.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)

        class Filter(object):

            def filter(self, record):
                return True

        test_filter = Filter()

        core.invoke_command('exopy.app.logging.add_filter',
                            {'id': 'filter', 'filter': test_filter,
                             'handler_id': 'ui'},
                            self)

        log_plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert log_plugin.filter_ids == [u'filter']
        assert log_plugin._filters == {u'filter': (test_filter, u'ui')}

        core.invoke_command('exopy.app.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert log_plugin.filter_ids == []
        assert log_plugin._filters == {}

    def test_filter3(self, logger):
        """Test adding an improper filter.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')

        core.invoke_command('exopy.app.logging.add_filter',
                            {'id': 'filter', 'filter': object(),
                             'handler_id': 'ui'},
                            self)

    def test_filter4(self, logger):
        """Test adding a filter to a non-existing handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')

        class Filter(object):

            def filter(self, record):
                return True

        core.invoke_command('exopy.app.logging.add_filter',
                            {'id': 'filter', 'filter': Filter(),
                             'handler_id': 'ui'},
                            self)

    def test_formatter(self, logger, exopy_qtbot):
        """Test setting the formatter of a handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        model = LogModel()
        handler = GuiHandler(model=model)
        core.invoke_command('exopy.app.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)

        formatter = logging.Formatter('test : %(message)s')
        core.invoke_command('exopy.app.logging.set_formatter',
                            {'formatter': formatter, 'handler_id': 'ui'},
                            self)

        logger.info('test')

        def assert_text():
            assert model.text == 'test : test\n'
        exopy_qtbot.wait_until(assert_text)

    def test_formatter2(self, logger, exopy_qtbot):
        """Test setting the formatter of a non existing handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')

        formatter = logging.Formatter('test : %(message)s')
        core.invoke_command('exopy.app.logging.set_formatter',
                            {'formatter': formatter,
                             'handler_id': 'non-existing'},
                            self)

        exopy_qtbot.wait(10)

    def test_start_logging1(self, app_dir):
        """Test startup function when redirection of sys.stdout is required

        """
        cmd_args = CMDArgs()
        cmd_args.nocapture = False
        old = sys.stdout

        app = self.workbench.get_plugin('exopy.app')
        app.run_app_startup(cmd_args)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        try:
            assert os.path.isdir(os.path.join(app_dir, 'logs'))
            assert 'exopy.file_log' in plugin.handler_ids
            assert 'exopy.gui_log' in plugin.handler_ids
            assert plugin.gui_model
            assert isinstance(sys.stdout, StreamToLogRedirector)
            assert isinstance(sys.stderr, StreamToLogRedirector)
        finally:
            sys.stdout = old

    def test_start_logging2(self, app_dir):
        """Test startup function when redirection of sys.stdout is not required

        """
        cmd_args = CMDArgs()
        cmd_args.nocapture = True
        old = sys.stdout

        app = self.workbench.get_plugin('exopy.app')
        app.run_app_startup(cmd_args)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        try:
            assert os.path.isdir(os.path.join(app_dir, 'logs'))
            assert 'exopy.file_log' in plugin.handler_ids
            assert 'exopy.gui_log' in plugin.handler_ids
            assert plugin.gui_model
            # Fail in no capture mode (unknown reason).
            assert not isinstance(sys.stdout, StreamToLogRedirector)
            assert not isinstance(sys.stderr, StreamToLogRedirector)
        finally:
            sys.stdout = old

    def test_display_current_log(self, app_dir, exopy_qtbot):
        """Test the log display window

        """
        cmd_args = CMDArgs()
        cmd_args.nocapture = True

        app = self.workbench.get_plugin('exopy.app')
        app.run_app_startup(cmd_args)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        with handle_dialog(exopy_qtbot):
            core.invoke_command('exopy.app.logging.display_current_log', {}, self)
