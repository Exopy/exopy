# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the plugin tools behaviours.

"""
from pytest import raises
import enaml
from enaml.workbench.api import Workbench


with enaml.imports():
    from .plugin_tools_testing import (ModularManifest, Contributor1,
                                       Contributor1bis, Contributor2,
                                       Contributor3, Contributor4,
                                       PLUGIN_ID)


class TestExtensionsCollector(object):
    """Test the ExtensionsCollector behaviour.

    """
    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(ModularManifest())

    def test_registation1(self):
        """Test that plugin registered before starting the plugin are well
        detected

        """

        c = Contributor1()
        self.workbench.register(c)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert 'contrib1.contrib' in plugin.contribs.contributions

        self.workbench.unregister(c.id)

        assert 'contrib1.contrib' not in plugin.contribs.contributions
        assert not plugin.contribs._extensions

    def test_registration2(self):
        """Test contribs update when a new plugin is registered.

        """

        plugin = self.workbench.get_plugin(PLUGIN_ID)
        c = Contributor1()
        self.workbench.register(c)

        assert 'contrib1.contrib' in plugin.contribs.contributions

        self.workbench.unregister(c.id)

        assert 'contrib1.contrib' not in plugin.contribs.contributions

    def test_factory(self):
        """Test getting the Contribution declaration from a factory.

        """

        c = Contributor2()
        self.workbench.register(c)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert 'contrib2.contrib' in plugin.contribs.contributions

        self.workbench.unregister(c.id)

        assert 'contrib2.contrib' not in plugin.contribs.contributions

    def test_errors1(self):
        """Test uniqueness of contribution id.

        """

        self.workbench.register(Contributor1())
        self.workbench.register(Contributor1bis())
        with raises(ValueError):
            self.workbench.get_plugin(PLUGIN_ID)

    def test_check_errors2(self):
        """Test use of validate_ext.

        """

        self.workbench.register(Contributor3())
        with raises(ValueError):
            self.workbench.get_plugin(PLUGIN_ID)

    def test_check_errors3(self):
        """Test enforcement of type when using factory.

        """

        self.workbench.register(Contributor4())
        with raises(TypeError):
            self.workbench.get_plugin(PLUGIN_ID)

    def test_declared_by(self):
        """Test getting the extension declaring a particular contribution.

        """
        c = Contributor1()
        self.workbench.register(c)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert plugin.contribs.contributed_by('contrib1.contrib') is \
            c.extensions[0]
