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
from inspect import cleandoc
from funcsigs import signature
from traceback import format_exc

from ...utils.configobj_ops import flatten_config
from ...utils.walks import flatten_walk
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

    if not contrib.collect:
        msg = "BuildDependency '%s' does not declare a collect function"
        return False, msg % contrib.id

    if len(signature(contrib.collect).parameters) != 2:
        msg = cleandoc("""BuildDependency '%s' collect function must have
                       signature (workbench, flat_walk)""")
        return False, msg % contrib.id

    return True, ''


def validate_runtime_dep(contrib):
    """Validate that a runtime dependency does declare everything it should.

    """
    if not contrib.walk_members and not contrib.walk_callables:
        msg = "RuntimeDependency '%s' does not declare any dependencies"
        return False, msg % contrib.id

    if not contrib.collect:
        msg = "RuntimeDependency '%s' does not declare a collect function"
        return False, msg % contrib.id

    if len(signature(contrib.collect).parameters) != 3:
        msg = cleandoc("""BuildDependency '%s' collect function must have
                       signature (workbench, flat_walk, plugin_id)""")
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

    def collect_dependencies(self, obj, dependencies=['build', 'runtime'],
                             ids=[], caller=None):
        """Build a dict of dependencies for a given obj.

        NB : This assumes the obj has a walk method similar to the one found
        in ComplexTask

        Parameters
        ----------
        obj : object with a walk method
            Obj for which dependencies should be computed.

        dependencies : {['build'], ['runtime'], ['build', 'runtime']}
            Kind of dependencies which should be gathered.

        ids : list, optional
            List of dependencies ids to use when collecting.

        caller : optional
            Calling plugin. Used for some runtime dependencies needing to know
            the ressource owner.

        Returns
        -------
        result : bool
            Flag indicating the success of the operation.

        dependencies : dict
            In case of success:
            - Dicts holding all the classes or other dependencies to build, run
              or build and run a task without any access to the workbench.
              If a single kind of dependencies is requested a single dict is
              returned otherwise a tuple of two is returned one for the build
              ones and one for the runtime ones

            Otherwise:
            - dict holding the id of the dependency and the asssociated
              error message.

        """
        # Use a set to avoid collecting several times the same entry, which
        # could happen if an entry is both a build and a runtime dependency.
        members = set()
        callables = {}
        if 'runtime' in dependencies and caller is None:
            msg = '''Cannot collect runtime dependencies without knowing the
                caller plugin'''
            return False, {'runtime': cleandoc(msg)}

        if 'build' in dependencies:
            if ids:
                b = self.build_deps.contributions
                build_deps = [dep for id, dep in b.iteritems()
                              if id in ids]
            else:
                build_deps = self.build_deps.contributions.values()

            for build_dep in build_deps:
                members.update(set(build_dep.walk_members))

        if 'runtime' in dependencies:
            if ids:
                r = self.run_deps.contributions
                runtime_deps = [dep for id, dep in r.iteritems()
                                if id in ids]
            else:
                runtime_deps = self.run_deps.contributions.values()

            for runtime_dep in runtime_deps:
                members.update(set(runtime_dep.walk_members))
                callables.update(runtime_dep.walk_callables)

        walk = obj.walk(members, callables)
        flat_walk = flatten_walk(walk, list(members) + callables.keys())

        deps = ({}, {})
        errors = {}
        if 'build' in dependencies:
            for build_dep in build_deps:
                try:
                    deps[0].update(build_dep.collect(self.workbench,
                                                     flat_walk))
                except Exception:
                    errors[build_dep.id] = format_exc()

        if 'runtime' in dependencies:
            for runtime_dep in runtime_deps:
                try:
                    deps[1].update(runtime_dep.collect(self.workbench,
                                                       flat_walk, caller))
                except Exception:
                    errors[runtime_dep.id] = format_exc()

        if errors:
            return False, errors

        if 'build' in dependencies and 'runtime' in dependencies:
            return True, (deps[0], deps[1])
        elif 'build' in dependencies:
            return True, deps[0]
        else:
            return True, deps[1]

    def collect_build_dep_from_config(self, config):
        """Read a ConfigObj object to determine all the build dependencies of
        an object and get them in a dict.

        Parameters
        ----------
        config : Section
            Section representing the object.

        Returns
        -------
        result : bool
            Flag indicating the success of the operation.

        build_dep : nested dict or None
            In case of success:
            - Dictionary holding all the build dependencies of an obj.
              With this dict and the config the obj can be reconstructed
              without accessing the workbech.
            Otherwise:
            - dict holding the id of the dependency and the asssociated
              error message.

        """
        members = []
        for build_dep in self.build_deps.contributions.values():
            members.extend(build_dep.walk_members)

        flat_config = flatten_config(config, members)

        build_deps = {}
        errors = {}
        for build_dep in self.build_deps.contributions.values():
            try:
                build_deps.update(build_dep.collect(self.workbench,
                                                    flat_config))
            except Exception:
                    errors[build_dep.id] = format_exc()

        if errors:
            return False, errors
        else:
            return True, build_deps
