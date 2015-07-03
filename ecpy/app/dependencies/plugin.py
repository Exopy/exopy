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
from collections import defaultdict

from configobj import Section

from ...utils.configobj_ops import traverse_config
from ...utils.plugin_tools import ExtensionsCollector

from .dependencies import BuildDependency, RuntimeDependency


BUILD_DEP_POINT = 'ecpy.app.dependencies.build'

RUNTIME_DEP_POINT = 'ecpy.app.dependencies.runtime'


def validate_build_dep(contrib):
    """Validate that a runtime dependency does declare everything it should.

    """
    func = getattr(contrib.collect, 'im_func',
                   getattr(contrib.collect, '__func__', None))
    if not func or func is BuildDependency.collect.__func__:
        msg = "BuildDependency '%s' does not declare a collect function"
        return False, msg % contrib.id

    return True, ''


def validate_runtime_dep(contrib):
    """Validate that a runtime dependency does declare everything it should.

    """
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
            gen = traverse_config(obj)
            getter = getitem
        else:
            gen = obj.traverse()
            getter = getattr

        builds = self.build_deps.contributions
        runtimes = self.run_deps.contributions

        deps = (defaultdict(dict), defaultdict(dict))
        errors = (defaultdict(dict), defaultdict(dict))
        need_runtime = 'runtime' in dependencies
        if need_runtime and not owner:
            gen = ()
            msg = ('A owner plugin must be specified when collecting' +
                   'runtime  dependencies.')
            errors[1]['owner'] = msg

        for component in gen:
            dep_type = getter(component, 'dep_type')
            try:
                collector = builds[dep_type]
            except KeyError:
                msg = 'No matching collector for dep_type : {}'
                errors[0][dep_type] = msg.format(dep_type)
                break
            run_ids = collector.collect(self.workbench, component,
                                        getter, deps[0], errors[0])

            if need_runtime and run_ids:
                if any(r not in runtimes for r in run_ids):
                    msg = 'No collector matching the ids : %s'
                    errors[1]['runtime'] = msg % [r for r in run_ids
                                                  if r not in runtimes]
                    break
                for r in run_ids:
                    runtimes[r].collect(self.workbench, owner, component,
                                        getter, deps[1], errors[1])

        res = not any(errors)
        answer = errors if any(errors) else deps

        if 'build' in dependencies and 'runtime' in dependencies:
            return res, answer
        elif 'build' in dependencies:
            return res, answer[0]
        else:
            return res, answer[1]
