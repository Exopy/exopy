# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the plugin tools behaviours.

"""
import pytest
import enaml
from enaml.workbench.api import Workbench

from exopy.utils.plugin_tools import make_extension_validator

from exopy.testing.util import handle_dialog

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from .plugin_tools_testing import (ExtensionManifest,
                                       Contribution, DContribution,
                                       Contributor1, Contributor2,
                                       Contributor3, Contributor4,
                                       DeclaratorManifest,
                                       DContributor1, DContributor2,
                                       DContributor3, DContributor4,
                                       DContributor5,
                                       PLUGIN_ID)


def test_make_extension_validator():
    """Test the building of generic extension validators.

    """
    c_validator = make_extension_validator(Contribution, ('new',))
    assert c_validator(Contribution())[0] is False
    assert c_validator(DContribution())[0] is False
    assert c_validator(DContribution(description='test'))[0] is True

    class CContribution(Contribution):

        def new(self, workbench):
            return 1

    assert c_validator(CContribution())[0] is False
    assert c_validator(CContribution(description='test'))[0] is True


class TestExtensionsCollector(object):
    """Test the ExtensionsCollector behaviour.

    """
    def setup_method(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(ErrorsManifest())
        self.workbench.register(ExtensionManifest())

    def test_registation1(self, exopy_qtbot):
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

        plugin.contribs.stop()
        assert not plugin.contribs.contributions

    def test_registration2(self, exopy_qtbot):
        """Test contribs update when a new plugin is registered.

        """
        self.workbench.register(Contributor2())
        plugin = self.workbench.get_plugin(PLUGIN_ID)
        c = Contributor1()
        self.workbench.register(c)

        assert 'contrib1.contrib' in plugin.contribs.contributions

        self.workbench.unregister(c.id)

        assert 'contrib1.contrib' not in plugin.contribs.contributions

    def test_factory(self, exopy_qtbot):
        """Test getting the Contribution declaration from a factory.

        """
        c = Contributor2()
        self.workbench.register(c)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert 'contrib2.contrib' in plugin.contribs.contributions

        self.workbench.unregister(c.id)

        assert 'contrib2.contrib' not in plugin.contribs.contributions

    @pytest.mark.ui
    def test_errors1(self, exopy_qtbot):
        """Test uniqueness of contribution id.

        """

        self.workbench.register(Contributor1())
        self.workbench.register(Contributor1(id='bis'))
        self.workbench.register(Contributor1(id='ter'))
        with handle_dialog(exopy_qtbot):
            self.workbench.get_plugin(PLUGIN_ID)

    @pytest.mark.ui
    def test_check_errors2(self, exopy_qtbot):
        """Test use of validate_ext.

        """

        self.workbench.register(Contributor3())
        with handle_dialog(exopy_qtbot):
            self.workbench.get_plugin(PLUGIN_ID)

    def test_check_errors3(self, exopy_qtbot):
        """Test enforcement of type when using factory.

        """

        self.workbench.register(Contributor4())
        with handle_dialog(exopy_qtbot):
            self.workbench.get_plugin(PLUGIN_ID)

    def test_declared_by(self):
        """Test getting the extension declaring a particular contribution.

        """
        c = Contributor1()
        self.workbench.register(c)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert plugin.contribs.contributed_by('contrib1.contrib') is \
            c.extensions[0]


class TestDeclaratorCollector(object):
    """Test the ExtensionsCollector behaviour.

    """
    def setup_method(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(ErrorsManifest())
        self.workbench.register(DeclaratorManifest())

    def test_registation1(self, exopy_qtbot):
        """Test that plugin registered before starting the plugin are well
        detected

        """
        d = DContributor1()
        self.workbench.register(d)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert 'contrib1' in plugin.contribs.contributions

        self.workbench.unregister(d.id)

        assert not plugin.contribs.contributions
        assert not plugin.contribs._extensions

    def test_registration2(self, exopy_qtbot):
        """Test contribs update when a new plugin is registered.

        """
        class Witness(object):

            called = 0

            def see(self, change):
                print('r')
                self.called += 1

        w = Witness()

        self.workbench.register(DContributor2())
        plugin = self.workbench.get_plugin(PLUGIN_ID)
        plugin.contribs.observe('contributions', w.see)

        d = DContributor1()
        self.workbench.register(d)

        assert 'contrib1' in plugin.contribs.contributions
        assert w.called == 1

        self.workbench.unregister(d.id)

        assert 'contrib1' not in plugin.contribs.contributions
        assert w.called == 2

        plugin.contribs.stop()

        assert not plugin.contribs.contributions
        assert w.called == 2
        assert not plugin.contribs._extensions

    def test_factory(self, exopy_qtbot):
        """Test getting the TestDeclarator declaration from a factory.

        """
        d = DContributor2()
        self.workbench.register(d)
        plugin = self.workbench.get_plugin(PLUGIN_ID)

        assert 'contrib2' in plugin.contribs.contributions

        self.workbench.unregister(d.id)

        assert not plugin.contribs.contributions

    def test_check_errors1(self, exopy_qtbot):
        """Test enforcement of type when using factory.

        """

        self.workbench.register(DContributor3())
        with handle_dialog(exopy_qtbot):
            self.workbench.get_plugin(PLUGIN_ID)

    @pytest.mark.ui
    def test_declarator_failed_registration(self, exopy_qtbot):
        """Test handling of error when a declarator fail to register.

        """
        self.workbench.register(DContributor4())
        with handle_dialog(exopy_qtbot):
            self.workbench.get_plugin(PLUGIN_ID)

    @pytest.mark.ui
    def test_unsatifiable_requirement(self, exopy_qtbot):
        """Test the case of a declarator always adding itself to _deflayed.

        """
        self.workbench.register(DContributor5())
        with handle_dialog(exopy_qtbot):
            self.workbench.get_plugin(PLUGIN_ID)
