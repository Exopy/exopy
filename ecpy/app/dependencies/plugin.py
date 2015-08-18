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

from atom.api import Atom, Typed
from enaml.workbench.api import Plugin
from operator import getitem
from collections import defaultdict

from configobj import Section

from ...utils.configobj_ops import traverse_config
from ...utils.plugin_tools import ExtensionsCollector, make_extension_validator

from .dependencies import BuildDependency, RuntimeDependency


BUILD_DEP_POINT = 'ecpy.app.dependencies.build'

RUNTIME_DEP_POINT = 'ecpy.app.dependencies.runtime'


def clean_dict(mapping):
    """Keep only the non False entry from a dict.

    """
    return {k: v for k, v in mapping.iteritems() if v}


class BuildContainer(Atom):
    """Class used to store infos about collected build dependencies.

    """
    #: Dictionary storing the collected dependencies, grouped by id.
    dependencies = Typed(dict)

    #: Dictionary storing the errors which occured during collection.
    errors = Typed(dict)

    def clean(self):
        """Remove all empty entries from dictionaries.

        """
        self.dependencies = clean_dict(self.dependencies)
        self.errors = clean_dict(self.errors)

    def _default_dependencies(self):
        return defaultdict(dict)

    def _default_errors(self):
        return defaultdict(dict)


class RuntimeContainer(BuildContainer):
    """Class used to store infos about collected runtime dependencies.

    """
    #: Runtime dependencies which exists but are currently used by another
    #: part of the application and hence are unavailable.
    unavailable = Typed(dict)

    def clean(self):
        """Remove all empty entries from dictionaries.

        """
        super(RuntimeContainer, self).clean()
        self.unavailable = clean_dict(self.unavailable)

    def _default_unavailable(self):
        return defaultdict(set)


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
        checker = make_extension_validator(BuildDependency, ('collect',), ())
        self.build_deps = ExtensionsCollector(workbench=self.workbench,
                                              point=BUILD_DEP_POINT,
                                              ext_class=BuildDependency,
                                              validate_ext=checker)
        self.build_deps.start()

        checker = make_extension_validator(RuntimeDependency, ('collect',), ())
        self.run_deps = ExtensionsCollector(workbench=self.workbench,
                                            point=RUNTIME_DEP_POINT,
                                            ext_class=RuntimeDependency,
                                            validate_ext=checker)
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
            build dependencies can be retrieved from a `configobj.Section`
            object.

        owner : optional
            Calling plugin id. Used for some runtime dependencies needing to
            know the ressource owner.

        Returns
        -------
        dependencies : BuildContainer | RuntimeContainer | tuple
            BuildContainer, RuntimeContaineror tuple of both according to
            the requested dependencies.

        """
        if isinstance(obj, Section):
            gen = traverse_config(obj)
            getter = getitem
        else:
            gen = obj.traverse()
            getter = getattr

        builds = self.build_deps.contributions
        runtimes = self.run_deps.contributions

        build_deps = BuildContainer()
        runtime_deps = RuntimeContainer()
        need_runtime = 'runtime' in dependencies
        if need_runtime and not owner:
            gen = ()
            msg = ('A owner plugin must be specified when collecting ' +
                   'runtime dependencies.')
            runtime_deps.errors['owner'] = msg
            # Next part is skipped as gen is empty

        for component in gen:
            dep_type = getter(component, 'dep_type')
            try:
                collector = builds[dep_type]
            except KeyError:
                msg = 'No matching collector for dep_type : {}'
                build_deps.errors[dep_type] = msg.format(dep_type)
                break
            run_ids = collector.collect(self.workbench, component, getter,
                                        build_deps.dependencies[collector.id],
                                        build_deps.errors[collector.id])

            if need_runtime and run_ids:
                if any(r not in runtimes for r in run_ids):
                    msg = 'No collector matching the ids : %s'
                    missings = [r for r in run_ids if r not in runtimes]
                    runtime_deps.errors['runtime'] = msg % missings
                    break
                for r in run_ids:
                    runtimes[r].collect(self.workbench, owner, component,
                                        getter, runtime_deps.dependencies[r],
                                        runtime_deps.unavailable[r],
                                        runtime_deps.errors[r])

        if 'build' in dependencies and 'runtime' in dependencies:
            build_deps.clean()
            runtime_deps.clean()
            return build_deps, runtime_deps
        elif 'build' in dependencies:
            build_deps.clean()
            return build_deps
        else:
            runtime_deps.clean()
            return runtime_deps

    def request_runtimes(self, owner, dependencies):
        """Request the right to use the listed dependencies.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        owner : unicode
            Id of the plugin requesting the ressources.

        dependencies : dict
            Dictionary containing the runtime dependencies to request organised
            by id.

        """
        runtimes = self.run_deps.contributions
        r_deps = RuntimeContainer(dependencies=dependencies)
        for dep_id in dependencies:
            if dep_id not in runtimes:
                msg = 'No collector found for %s'
                r_deps.errors[dep_id] = msg % dep_id
                continue
            runtimes[dep_id].request(self.workbench, owner,
                                     dependencies[dep_id],
                                     r_deps.unavailable[dep_id],
                                     r_deps.errors[dep_id])

        return r_deps

    def release_runtimes(self, owner, dependencies):
        """Release runtime dependencies previously acquired (collected).

        Parameters
        ----------
        owner : unicode
            Id of the plugin releasing the ressources.

        dependencies : dict
            Dictionary containing the runtime dependencies to release organised
            by id.

        """
        runtimes = self.run_deps.contributions
        for dep_id in dependencies:
            if dep_id not in runtimes:
                continue
            runtimes[dep_id].release(self.workbench, owner,
                                     dependencies[dep_id])
