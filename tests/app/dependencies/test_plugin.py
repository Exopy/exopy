# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test DependenciesManagerPLugin behavior.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from enaml.workbench.api import Workbench
from configobj import ConfigObj

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from ecpy.app.dependencies.manifest import DependenciesManifest

    from .dependencies_utils import (BuildDep, RuntimeDep)


COLLECT = 'ecpy.app.dependencies.collect'


@pytest.fixture
def dependent_object():

    class Obj(object):

        dep_type = 'test'

        val = 'r'

        run = 2

        def traverse(self):
            yield self

    return Obj()


class TestCollectingFromObject(object):
    """Test collecting dependencies of live objects.

    """

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(DependenciesManifest())
        self.workbench.register(BuildDep())
        self.workbench.register(RuntimeDep())

    def teardown(self):
        self.workbench.unregister('ecpy.app.dependencies')
        self.workbench.unregister('enaml.workbench.core')

    def test_collecting_build(self, dependent_object):
        """Test collecting only the build dependencies.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object})
        assert res
        assert dep.keys() == ['test']

    def test_collecting_runtime(self, dependent_object):
        """Test collecting only the runtime dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': ['runtime']},
                                       plugin)
        assert res
        assert dep.keys() == ['test_run']

    def test_collecting_all(self, dependent_object):
        """Test collecting all dependencies.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': ['build',
                                                                  'runtime'],
                                                 'owner': 'ecpy.test'})

        assert res
        assert dep[0].keys() == ['test']
        assert dep[1].keys() == ['test_run']

    def test_handling_errors(self, monkeypatch, dependent_object):
        """Test handling errors occuring when collecting dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'err', True)

        for r in plugin.run_deps.contributions.values():
            monkeypatch.setattr(r, 'err', True)

        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': ['build',
                                                                  'runtime'],
                                                 'owner': 'ecpy.test'})

        assert not res
        assert 'test' in dep[0] and 'test_run' in dep[1]

    def test_handling_missing_caller(self, dependent_object):
        """Test handling a missing caller when runtime dependencies are
        requested.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': ['runtime']})
        assert not res
        assert 'owner' in dep

    def test_handling_unknown_dep_type(self, dependent_object):
        """Test handling an unknown dep_type.

        """
        dependent_object.dep_type = 'Unknown'
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object})
        assert not res
        assert 'Unknown' in dep

    def test_handling_missing_runtime_collector(self, monkeypatch,
                                                dependent_object):
        """Test handling an unknown dep_type.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'run', ('unkwown',))

        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': ['runtime'],
                                                 'owner': object()})
        assert not res
        assert 'runtime' in dep


class TestCollectingFromConfig(object):
    """Test collecting dependencies from ConfigObj object.

    """

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(DependenciesManifest())
        self.workbench.register(BuildDep())

    def teardown(self):
        self.workbench.unregister('ecpy.app.dependencies')
        self.workbench.unregister('enaml.workbench.core')

    def test_collecting(self):
        """Test collecting from a dict-like object.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT,
                                       {'obj': ConfigObj({'val': '1',
                                                          'dep_type': 'test'})}
                                       )
        assert res
        assert dep.keys() == ['test']

    def test_handling_errors(self, monkeypatch):
        """Test handling errors occuring when collecting dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'err', True)

        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT,
                                       {'obj': ConfigObj({'val': '1',
                                                          'dep_type': 'test'})}
                                       )

        assert not res
        assert 'test' in dep
