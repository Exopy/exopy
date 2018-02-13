# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""App plugin extensions declarations.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from enaml.workbench.api import Workbench
from enaml.widgets.window import CloseEvent
import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.app_manifest import AppManifest
    from .app_helpers import (StartupContributor, ClosingContributor1,
                              ClosingContributor2, ClosedContributor)


class FalseWindow(object):
    """False WorkbenchWindow used for testing closing as need an object with
    a reference to the workbench.

    """

    def __init__(self, workbench):
        self.workbench = workbench


class TestAppPlugin(object):
    """Test the AppPlugin capabilities.

    """

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(AppManifest())
        self.workbench.register(CoreManifest())
        self.workbench.register(ErrorsManifest())

    def test_app_start_up(self):
        """Test running startups leading to new startup registrations.

        """
        manifest = StartupContributor()
        self.workbench.register(manifest)
        plugin = self.workbench.get_plugin('exopy.app')
        plugin.run_app_startup(object())

        assert manifest.called == ['test_nested.startup1', 'test.startup2',
                                   'test_nested.startup2']
        self.workbench.unregister('exopy.app')

    def test_closing(self):
        """Test that validation stops as soon as the event is rejected.

        """
        manifest1 = ClosingContributor1()
        manifest2 = ClosingContributor2()
        self.workbench.register(manifest1)
        self.workbench.register(manifest2)

        window = FalseWindow(self.workbench)

        plugin = self.workbench.get_plugin('exopy.app')
        ev = CloseEvent()
        plugin.validate_closing(window, ev)

        assert not ev.is_accepted()
        assert not manifest2.called or not manifest1.called

        manifest1.accept = True
        manifest2.accept = True

        plugin.validate_closing(window, ev)

        assert ev.is_accepted()
        assert manifest2.called

    def test_app_cleanup(self):
        """Test running the app cleanup.

        """
        manifest = ClosedContributor()
        self.workbench.register(manifest)
        plugin = self.workbench.get_plugin('exopy.app')
        plugin.run_app_cleanup()

        assert manifest.called == ['test_nested.closed1', 'test.closed2',
                                   'test_nested.closed2']

    def test_app_startup_registation(self):
        """Test the AppStartup discovery.

        """
        manifest = StartupContributor()
        self.workbench.register(manifest)

        plugin = self.workbench.get_plugin('exopy.app')
        assert len(plugin.startup.contributions) == 2
        assert len(plugin._start_heap) == 2

        self.workbench.unregister(manifest.id)

        assert not plugin.startup.contributions
        assert len(plugin._start_heap) == 0

    def test_app_closing_registation(self):
        """Test the AppClosing discovery.

        """
        manifest = ClosingContributor1()
        self.workbench.register(manifest)

        plugin = self.workbench.get_plugin('exopy.app')
        assert len(plugin.closing.contributions) == 1

        self.workbench.unregister(manifest.id)

        assert not plugin.closing.contributions

    def test_app_closed_registation(self):
        """Test the AppClosed discovery.

        """
        manifest = ClosedContributor()
        self.workbench.register(manifest)

        plugin = self.workbench.get_plugin('exopy.app')
        assert len(plugin.closed.contributions) == 2
        assert len(plugin._clean_heap) == 2

        self.workbench.unregister(manifest.id)

        assert not plugin.closed.contributions
        assert len(plugin._clean_heap) == 0
