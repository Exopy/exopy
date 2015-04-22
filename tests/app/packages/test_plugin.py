# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the PackagesPlugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from atom.api import Atom, Bool, Value, Unicode
from enaml.workbench.api import Workbench

with enaml.imports():
    from ecpy.app.app_manifest import AppManifest
    from ecpy.app.packages.manifest import PackagesManifest
    from .packages_utils import Manifest1, Manifest2


APP_ID = 'ecpy.app'
PACKAGES_ID = 'ecpy.app.packages'


@pytest.fixture
def workbench(request):
    """Create a workbench and register basic manifests.

    """
    workbench = Workbench()
    workbench.register(AppManifest())
    workbench.register(PackagesManifest())
    return workbench


def patch_pkg(monkey, answer):
    """Patch the pkg_resources.iter_entry_points function.

    """
    from ecpy.app.packages.plugin import pkg_resources
    monkey.setattr(pkg_resources, 'iter_entry_points', lambda x: answer)


class FalseEntryPoint(Atom):
    """False entry whose behavior can be customized.

    """
    #: Name of this entry point
    name = Unicode()

    #: Flag indicating whether the require method should raise an error.
    missing_require = Bool()

    #: List of manifest to return when load method is called.
    manifests = Value()

    def require(self):
        if self.missing_require:
            raise Exception()
        return True

    def load(self):
        return lambda: self.manifests


def test_collecting_registering_and_stopping(monkeypatch, workbench):
    """Test basic behavior of PackaggesPlugin.

    """
    patch_pkg(monkeypatch, [FalseEntryPoint(name='test',
                                            manifests=[Manifest1, Manifest2]),
                            FalseEntryPoint(name='test2',
                                            manifests=[])])

    app = workbench.get_plugin(APP_ID)
    app.run_app_startup(object())

    plugin = workbench.get_plugin(PACKAGES_ID)

    assert 'test' in plugin.packages
    assert 'test2' in plugin.packages
    assert 'ecpy.test1' in plugin.packages['test']
    assert 'ecpy.test2' in plugin.packages['test']
    assert (100, 0, 'ecpy.test1') in plugin._registered
    assert (0, 1, 'ecpy.test2') in plugin._registered
    assert workbench.get_plugin('ecpy.test1')
    assert workbench.get_plugin('ecpy.test2')

    workbench.unregister(PACKAGES_ID)

    with pytest.raises(ValueError):
        workbench.get_plugin('ecpy.test1')
    with pytest.raises(ValueError):
        workbench.get_plugin('ecpy.test2')


def test_unmet_requirement(monkeypatch, workbench):
    """Test loading an extension package for which some requirements are not
    met.

    """
    patch_pkg(monkeypatch, [FalseEntryPoint(name='test', missing_require=True),
                            FalseEntryPoint(name='test2',
                                            manifests=[])])

    app = workbench.get_plugin(APP_ID)
    app.run_app_startup(object())

    plugin = workbench.get_plugin(PACKAGES_ID)

    assert 'test' in plugin.packages
    assert 'test2' in plugin.packages
    assert 'load' in plugin.packages['test']
    assert not plugin._registered


def test_wrong_return_type(monkeypatch, workbench):
    """Test handling a wrong return type from the callable returned by load.

    """
    patch_pkg(monkeypatch, [FalseEntryPoint(name='test',
                                            manifests=Manifest1),
                            FalseEntryPoint(name='test2',
                                            manifests=[])])

    app = workbench.get_plugin(APP_ID)
    app.run_app_startup(object())

    plugin = workbench.get_plugin(PACKAGES_ID)

    assert 'test' in plugin.packages
    assert 'test2' in plugin.packages
    assert 'list' in plugin.packages['test']
    assert not plugin._registered


def test_non_manifest(monkeypatch, workbench):
    """Test handling a non PluginManifest in the list of manifests.

    """
    patch_pkg(monkeypatch, [FalseEntryPoint(name='test',
                                            manifests=[Manifest1, object]),
                            FalseEntryPoint(name='test2',
                                            manifests=[])])

    app = workbench.get_plugin(APP_ID)
    app.run_app_startup(object())

    plugin = workbench.get_plugin(PACKAGES_ID)

    assert 'test' in plugin.packages
    assert 'test2' in plugin.packages
    assert 'PluginManifests' in plugin.packages['test']
    assert not plugin._registered


def test_registering_issue(monkeypatch, workbench):
    """Test handling an error when registering a manifest.

    """
    patch_pkg(monkeypatch, [FalseEntryPoint(name='test',
                                            manifests=[Manifest1, Manifest1]),
                            FalseEntryPoint(name='test2',
                                            manifests=[])])

    app = workbench.get_plugin(APP_ID)

    app.run_app_startup(object())

    plugin = workbench.get_plugin(PACKAGES_ID)

    assert 'test' in plugin.packages
    assert 'test2' in plugin.packages
    assert 'ecpy.test1' in plugin.packages['test']
    assert len(plugin.packages['test']) == 1
