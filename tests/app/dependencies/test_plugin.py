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
        dep = core.invoke_command(COLLECT, {'obj': dependent_object})
        assert not dep.errors
        assert dep.dependencies.keys() == ['test']

    def test_collecting_runtime(self, dependent_object):
        """Test collecting only the runtime dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': plugin.manifest.id},
                                  )
        assert not dep.errors
        assert dep.dependencies.keys() == ['test_run']

    def test_collecting_unavailable_runtime(self, dependent_object,
                                            monkeypatch):
        """Test collecting only the runtime dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')

        for r in plugin.run_deps.contributions.values():
            monkeypatch.setattr(r, 'una', True)

        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': plugin.manifest.id},
                                  )
        assert not dep.errors
        assert dep.unavailable['test_run'] == {'run'}

    def test_collecting_all(self, dependent_object):
        """Test collecting all dependencies.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        b_dep, r_dep = core.invoke_command(COLLECT,
                                           {'obj': dependent_object,
                                            'dependencies': ['build',
                                                             'runtime'],
                                            'owner': 'ecpy.test'})

        assert not b_dep.errors and not r_dep.errors
        assert b_dep.dependencies.keys() == ['test']
        assert r_dep.dependencies.keys() == ['test_run']

    def test_handling_errors(self, monkeypatch, dependent_object):
        """Test handling errors occuring when collecting dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'err', True)

        for r in plugin.run_deps.contributions.values():
            monkeypatch.setattr(r, 'err', True)

        core = self.workbench.get_plugin('enaml.workbench.core')
        b_dep, r_dep = core.invoke_command(COLLECT,
                                           {'obj': dependent_object,
                                            'dependencies': ['build',
                                                             'runtime'],
                                            'owner': 'ecpy.test'})

        assert 'test' in b_dep.errors and 'test_run' in r_dep.errors

    def test_handling_missing_caller(self, dependent_object):
        """Test handling a missing caller when runtime dependencies are
        requested.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime']})
        assert 'owner' in dep.errors

    def test_handling_unknown_dep_type(self, dependent_object):
        """Test handling an unknown dep_type.

        """
        dependent_object.dep_type = 'Unknown'
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object})
        assert 'Unknown' in dep.errors

    def test_handling_missing_runtime_collector(self, monkeypatch,
                                                dependent_object):
        """Test handling an unknown dep_type.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'run', ('unkwown',))

        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': object()})
        assert 'runtime' in dep.errors

    def test_requesting_runtimes(self, dependent_object):
        """Test requesting runtimes dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': plugin.manifest.id},
                                  )
        dep = core.invoke_command('ecpy.app.dependencies.request_runtimes',
                                  {'dependencies': dep.dependencies,
                                   'owner': plugin.manifest.id},
                                  )

        assert dep.dependencies['test_run']['run'] == 1

    def test_requesting_runtimes_missing(self, monkeypatch, dependent_object):
        """Test requesting runtimes dependencies when a collector is missing.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': plugin.manifest.id},
                                  )

        for r in plugin.run_deps.contributions.values():
            monkeypatch.setattr(r, 'err', True)
        dep.dependencies['test_missing'] = {}
        dep = core.invoke_command('ecpy.app.dependencies.request_runtimes',
                                  {'dependencies': dep.dependencies,
                                   'owner': plugin.manifest.id},
                                  )

        assert 'test_run' in dep.errors
        assert 'test_missing' in dep.errors

    def test_requesting_runtimes_unavailable(self, monkeypatch,
                                             dependent_object):
        """Test requesting runtimes dependencies when a dependency is
        unavailable.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': plugin.manifest.id},
                                  )

        for r in plugin.run_deps.contributions.values():
            monkeypatch.setattr(r, 'una', True)

        dep = core.invoke_command('ecpy.app.dependencies.request_runtimes',
                                  {'dependencies': dep.dependencies,
                                   'owner': plugin.manifest.id},
                                  )

        assert 'test_run' in dep.unavailable

    def test_releasing_runtimes(self, dependent_object):
        """Test releasing runtime dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')
        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                            'dependencies': ['runtime'],
                                            'owner': plugin.manifest.id},
                                  )
        # Ensure that an unknown runtime won't crash
        dep.dependencies['rr'] = {}
        core.invoke_command('ecpy.app.dependencies.release_runtimes',
                            {'dependencies': dep.dependencies,
                             'owner': plugin.manifest.id},
                            )

        assert 'run' not in dep.dependencies['test_run']


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
        dep = core.invoke_command(COLLECT,
                                  {'obj': ConfigObj({'val': '1',
                                                     'dep_type': 'test'})}
                                  )
        assert dep.dependencies.keys() == ['test']

    def test_handling_errors(self, monkeypatch):
        """Test handling errors occuring when collecting dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'err', True)

        core = self.workbench.get_plugin('enaml.workbench.core')
        dep = core.invoke_command(COLLECT,
                                  {'obj': ConfigObj({'val': '1',
                                                     'dep_type': 'test'})}
                                  )

        assert 'test' in dep.errors
