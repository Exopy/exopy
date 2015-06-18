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

from types import MethodType

import pytest
import enaml
from enaml.workbench.api import Workbench
from configobj import ConfigObj

from ecpy.app.dependencies.dependencies import (BuildDependency,
                                                RuntimeDependency)

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from ecpy.app.dependencies.manifest import DependenciesManifest
    from ecpy.app.dependencies.plugin import (validate_build_dep,
                                              validate_runtime_dep)

    from .dependencies_utils import (BuildDep, RuntimeDep)


COLLECT = 'ecpy.app.dependencies.collect'

COLLECT_CONFIG = 'ecpy.app.dependencies.collect_from_config'


def test_validate_build_dep():
    """Check the validation of BuildDependency object.

    """
    class BDep(object):
        id = 'test'
    bdep = BDep()
    bdep.walk_members = None
    bdep.collect = BuildDependency.collect

    assert validate_build_dep(bdep)[0] is False
    assert 'dependencies' in validate_build_dep(bdep)[1]

    bdep.walk_members = ['t']
    assert validate_build_dep(bdep)[0] is False
    assert 'collect' in validate_build_dep(bdep)[1]

    bdep.collect = MethodType(lambda w, f: w, bdep)
    assert validate_build_dep(bdep)[0]


def test_validate_runtime_dep():
    """Check the validation of RuntimeDependency object.

    """
    class RDep(object):
        id = 'test'
    rdep = RDep()
    rdep.walk_members = None
    rdep.walk_callables = None
    rdep.collect = RuntimeDependency.collect

    assert validate_runtime_dep(rdep)[0] is False
    assert 'dependencies' in validate_runtime_dep(rdep)[1]

    rdep.walk_members = ['t']
    assert validate_runtime_dep(rdep)[0] is False
    assert 'collect' in validate_runtime_dep(rdep)[1]

    rdep.walk_members = None
    rdep.walk_callables = {1: 2}
    assert validate_runtime_dep(rdep)[0] is False
    assert 'collect' in validate_runtime_dep(rdep)[1]

    rdep.collect = MethodType(lambda w, f, p: w, rdep)
    assert validate_runtime_dep(rdep)[0]


@pytest.fixture
def dependent_object(request):

    class Obj(object):

        def walk(self, members, callables):
            return [{m: '' for m in members}, [{c: '' for c in callables}]]

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
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': ['build']})
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
                                                 'caller': 'ecpy.test'})

        assert res
        assert dep[0].keys() == ['test']
        assert dep[1].keys() == ['test_run']

    def test_collecting_by_id(self, dependent_object):
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'ids': ['test.build_dep'],
                                                 'caller': 'ecpy.test'})

        assert res
        assert dep[0].keys() == ['test']
        assert not dep[1]

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
                                                 'caller': 'ecpy.test'})

        assert not res
        assert 'test.build_dep' in dep and 'test.runtime_dep' in dep

    def test_handling_missing_caller(self):
        """Test handling a missing caller when runtime dependencies are
        requested.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT, {'obj': dependent_object,
                                                 'dependencies': 'runtime'})
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
        res, dep = core.invoke_command(COLLECT_CONFIG,
                                       {'config': ConfigObj()})
        assert res
        assert dep.keys() == ['test']

    def test_handling_errors(self, monkeypatch):
        """Test handling errors occuring when collecting dependencies.

        """
        plugin = self.workbench.get_plugin('ecpy.app.dependencies')

        for b in plugin.build_deps.contributions.values():
            monkeypatch.setattr(b, 'err', True)

        core = self.workbench.get_plugin('enaml.workbench.core')
        res, dep = core.invoke_command(COLLECT_CONFIG,
                                       {'config': ConfigObj()})

        assert not res
        assert 'test.build_dep' in dep
