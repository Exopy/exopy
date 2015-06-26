# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin handling dependencies declarations.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Typed
from enaml.workbench.api import Plugin
from operator import getitem

from configobj import Section

from ...utils.configobj_ops import traverse_config
from ...utils.plugin_tools import ExtensionsCollector

from .dependencies import BuildDependency, RuntimeDependency


BUILD_DEP_POINT = 'ecpy.app.dependencies.build'

RUNTIME_DEP_POINT = 'ecpy.app.dependencies.runtime'


def validate_build_dep(contrib):
    """Validate that a runtime dependency does declare everything it should.

    """
    if not contrib.walk_members:
        msg = "BuildDependency '%s' does not declare any dependencies"
        return False, msg % contrib.id

    func = getattr(contrib.collect, 'im_func',
                   getattr(contrib.collect, '__func__', None))
    if not func or func is BuildDependency.collect.__func__:
        msg = "BuildDependency '%s' does not declare a collect function"
        return False, msg % contrib.id

    return True, ''


def validate_runtime_dep(contrib):
    """Validate that a runtime dependency does declare everything it should.

    """
    if not contrib.walk_members and not contrib.walk_callables:
        msg = "RuntimeDependency '%s' does not declare any dependencies"
        return False, msg % contrib.id

    func = getattr(contrib.collect, 'im_func',
                   getattr(contrib.collect, '__func__', None))
    if not func or func is RuntimeDependency.collect.__func__:
        msg = "RuntimeDependency '%s' does not declare a collect function"
        return False, msg % contrib.id

    return True, ''


class DependenciesPlugin(Plugin):
    """Dependencies manager for the application.

    """
    #: Contributed build dependencies.
    build_deps = Typed(ExtensionsCollector)

    #: Contributed runtime dependencies.
    run_deps = Typed(ExtensionsCollector)

    def start(self):
        """Start the manager and load all contributions.

        """
        self.build_deps = ExtensionsCollector(workbench=self.workbench,
                                              point=BUILD_DEP_POINT,
                                              ext_class=BuildDependency,
                                              validate_ext=validate_build_dep)
        self.build_deps.start()

        self.run_deps = ExtensionsCollector(workbench=self.workbench,
                                            point=RUNTIME_DEP_POINT,
                                            ext_class=RuntimeDependency,
                                            validate_ext=validate_runtime_dep
                                            )
        self.run_deps.start()

    def stop(self):
        """Stop the manager.

        """
        self.build_deps.stop()
        self.run_deps.stop()

    def collect_dependencies(self, obj, dependencies=['build'], owner=None):
        """Build a dictionary of dependencies for a given object.

        The object must either be a configobj.Section object or have a traverse
        method yielding the object and all its subcomponent suceptible to add
        more dependencies.

        Parameters
        ----------
        obj : object with a walk method
            Obj for which dependencies should be computed.

        dependencies : {['build'], ['runtime'], ['build', 'runtime']}
            Kind of dependencies which should be gathered. Note that only
            build dependencies can be retrieved from a configobj.Section
            object.

        owner : optional
            Calling plugin. Used for some runtime dependencies needing to know
            the ressource owner.

        Returns
        -------
        result : bool
            Flag indicating the success of the operation.

        dependencies : dict|tuple[dict]
            In case of success:
            - Dicts holding all the classes or other dependencies to build, run
              or build and run the object without any access to the workbench.
              If a single kind of dependencies is requested a single dict is
              returned otherwise a tuple of two is returned one for the build
              ones and one for the runtime ones

            Otherwise:
            - dict holding the id of the dependency and the asssociated
              error message.

        """
        if isinstance(obj, Section):
            ite = traverse_config(obj)
            getter = getitem
        else:
            ite = obj.traverse()
            getter = getattr

        builds = self.build_deps.contributions
        runtimes = self.runtime_deps.contributions

        deps = ({}, {})
        errors = ({}, {})
        need_runtime = 'runtime' in dependencies
        for component in ite:
            dep_type = getter(component, 'dep_type')
            runtimes = builds[dep_type].collect(self.workbench, component,
                                                getter, deps[0], errors[0])

            if need_runtime:
                for runtime in runtimes:
                    runtime.colect(self.workbench, owner, component, getter,
                                   deps[1], errors[1])

        if any(errors):
            if 'build' in dependencies and 'runtime' in dependencies:
                return False, errors
            elif 'build' in dependencies:
                return False, errors[0]
            else:
                return False, errors[1]

        if 'build' in dependencies and 'runtime' in dependencies:
            return True, deps
        elif 'build' in dependencies:
            return True, deps[0]
        else:
            return True, deps[1]
