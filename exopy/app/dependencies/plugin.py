# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin handling dependencies declarations.

"""
from collections import defaultdict

from configobj import Section
from atom.api import Atom, Typed
from enaml.workbench.api import Plugin

from ...utils.traceback import format_exc
from ...utils.configobj_ops import traverse_config
from ...utils.plugin_tools import ExtensionsCollector, make_extension_validator

from .dependencies import (BuildDependency, RuntimeDependencyAnalyser,
                           RuntimeDependencyCollector)


BUILD_DEP_POINT = 'exopy.app.dependencies.build'

RUNTIME_DEP_ANALYSE_POINT = 'exopy.app.dependencies.runtime_analyse'

RUNTIME_DEP_COLLECT_POINT = 'exopy.app.dependencies.runtime_collect'


def clean_dict(mapping):
    """Keep only the non False entry from a dict.

    """
    return {k: v for k, v in mapping.items() if v}


class BuildContainer(Atom):
    """Class used to store infos about collected build dependencies.

    """
    #: Dictionary storing the collected dependencies, grouped by id.
    dependencies = Typed(dict)

    #: Dictionary storing the errors which occurred during collection.
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

    #: Contributed runtime dependencies analysers.
    run_deps_analysers = Typed(ExtensionsCollector)

    #: Contributed runtime dependencies collectors.
    run_deps_collectors = Typed(ExtensionsCollector)

    def start(self):
        """Start the manager and load all contributions.

        """
        checker = make_extension_validator(BuildDependency,
                                           ('analyse', 'validate', 'collect'),
                                           ())
        self.build_deps = ExtensionsCollector(workbench=self.workbench,
                                              point=BUILD_DEP_POINT,
                                              ext_class=BuildDependency,
                                              validate_ext=checker)
        self.build_deps.start()

        checker = make_extension_validator(RuntimeDependencyAnalyser,
                                           ('analyse',), ('collector_id',))
        self.run_deps_analysers =\
            ExtensionsCollector(workbench=self.workbench,
                                point=RUNTIME_DEP_ANALYSE_POINT,
                                ext_class=RuntimeDependencyAnalyser,
                                validate_ext=checker)

        self.run_deps_analysers.start()

        checker = make_extension_validator(RuntimeDependencyCollector,
                                           ('validate', 'collect'), ())
        self.run_deps_collectors =\
            ExtensionsCollector(workbench=self.workbench,
                                point=RUNTIME_DEP_COLLECT_POINT,
                                ext_class=RuntimeDependencyCollector,
                                validate_ext=checker)
        self.run_deps_collectors.start()

    def stop(self):
        """Stop the manager.

        """
        self.build_deps.stop()
        self.run_deps_analysers.stop()
        self.run_deps_collectors.stop()

    def analyse_dependencies(self, obj, dependencies=['build']):
        """Analyse the dependencies of a given object.

        The object must either be a configobj.Section object or have a traverse
        method yielding the object and all its subcomponent suceptible to add
        more dependencies.

        Parameters
        ----------
        obj : object
            Obj whose dependencies should be analysed.

        dependencies : {['build'], ['runtime'], ['build', 'runtime']}
            Kind of dependencies which should be gathered. Note that only
            build dependencies can be retrieved from a `configobj.Section`
            object.

        Returns
        -------
        dependencies : BuildContainer | RuntimeContainer | tuple
            BuildContainer, RuntimeContaineror tuple of both according to
            the requested dependencies.

        """
        # Identify the kind of object and what getter to use when analysing it.
        # and create the generator traversing the object.
        if isinstance(obj, Section):
            gen = traverse_config(obj)
            getter = dict.get
        else:
            gen = obj.traverse()
            getter = getattr

        # Get the declared build and runtime dependencies analysers.
        builds = self.build_deps.contributions
        runtimes_a = self.run_deps_analysers.contributions
        runtimes_c = self.run_deps_collectors.contributions
        runtimes_a = {k: v for k, v in runtimes_a.items()
                      if v.collector_id in runtimes_c}

        build_deps = BuildContainer(dependencies=defaultdict(set))
        runtime_deps = RuntimeContainer(dependencies=defaultdict(set))
        need_runtime = 'runtime' in dependencies

        for component in gen:
            dep_type = getter(component, 'dep_type', None)
            if dep_type is None:
                continue
            try:
                collector = builds[dep_type]
            except KeyError:
                msg = 'No matching collector for dep_type : {}'
                build_deps.errors[dep_type] = msg.format(dep_type)
                break

            c_id = collector.id
            try:
                run_ids = collector.analyse(self.workbench, component, getter,
                                            build_deps.dependencies[c_id],
                                            build_deps.errors[c_id])
            except Exception:
                build_deps.errors[c_id] =\
                    'An unhandled exception occured : \n%s' % format_exc()
                break

            if need_runtime and run_ids:
                if any(r not in runtimes_a for r in run_ids):
                    msg = 'No analyser matching the ids : %s'
                    missings = [r for r in run_ids if r not in runtimes_a]
                    if runtimes_a != self.run_deps_analysers.contributions:
                        add = ('\nThe following registered analysers do not '
                               'match a known collector : %s')
                        all_analysers = self.run_deps_analysers.contributions
                        add = add % [k for k in all_analysers
                                     if k not in runtimes_a]
                        msg += add
                    runtime_deps.errors['runtime'] = msg % missings
                    break
                for r in run_ids:
                    analyser = runtimes_a[r]
                    c_id = analyser.collector_id
                    try:
                        analyser.analyse(self.workbench, component,
                                         runtime_deps.dependencies[c_id],
                                         runtime_deps.errors[c_id])
                    except Exception:
                        runtime_deps.errors[r] =\
                            ('An unhandled exception occured : \n%s' %
                             format_exc())

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

    def validate_dependencies(self, kind, dependencies):
        """Validate that a set of dependencies is valid (ie exists).

        Parameters
        ----------
        kind : {'build', 'runtime'}
            Kind of dependency to validate.

        dependencies : dict
            Dictionary of dependencies sorted by id. This is typically the
            content of the dependencies attribute of BuildContainer or
            RuntimeContainer.

        Returns
        -------
        result : bool
            Boolean indicating whether or not all dependencies are valid.

        errors : dict
            Dictionary containing the errors which occured. Those are stored
            by dependency id and by dependency.

        """
        if kind == 'build':
            validators = self.build_deps.contributions
            container = BuildContainer()  # Used simply for its clean method
        elif kind == 'runtime':
            validators = self.run_deps_collectors.contributions
            container = RuntimeContainer()  # Used simply for its clean method
        else:
            raise ValueError("kind argument must be 'build' or 'runtime' not :"
                             " %s" % kind)

        for dep_id in dependencies:
            if dep_id not in validators:
                msg = 'No validator found for this kind of dependence.'
                container.errors[dep_id] = msg
                continue
            try:
                validators[dep_id].validate(self.workbench,
                                            dependencies[dep_id],
                                            container.errors[dep_id])
            except Exception:
                container.errors[dep_id] =\
                    'An unhandled exception occured :\n%s' % format_exc()

        container.clean()
        return not container.errors, container.errors

    def collect_dependencies(self, kind, dependencies, owner=None):
        """Collect a set of dependencies.

        For runtime dependencies if permissions are necessary to use a
        dependence they are requested and should released when they are no
        longer needed.

        Parameters
        ----------
        kind : {'build', 'runtime'}
            Kind of dependency to validate.

        dependencies : dict
            Dictionary of dependencies sorted by id. This is typically the
            content of the dependencies attribute of BuildContainer or
            RuntimeContainer.

        owner : unicode, optional
            Calling plugin id. Used for some runtime dependencies needing to
            know the ressource owner.

        Returns
        -------
        dependencies : BuildContainer | RuntimeContainer | tuple
            BuildContainer, RuntimeContainer or tuple of both according to
            the requested dependencies.

        """
        # Create a dictionary for each dep_id whose values are None and will
        # be replaced by the collected dependencies after collections.
        dependencies = {k: dict.fromkeys(v)
                        for k, v in dependencies.items()}

        if kind == 'build':
            collectors = self.build_deps.contributions
            container = BuildContainer()

            def collect(dep_id):
                """Collect dependencies matching the specified id.

                """
                try:
                    collectors[dep_id].collect(self.workbench,
                                               dependencies[dep_id],
                                               container.errors[dep_id])
                except Exception:
                    container.errors[dep_id] =\
                        'An unhandled exception occured :\n%s' % format_exc()

        elif kind == 'runtime':
            collectors = self.run_deps_collectors.contributions
            container = RuntimeContainer()
            if not owner:
                dependencies = ()
                msg = ('A owner plugin must be specified when collecting '
                       'runtime dependencies.')
                container.errors['owner'] = msg
                # Next part is skipped as dependencies is empty

            def collect(dep_id):
                """Collect dependencies matching the specified id.

                """
                try:
                    collectors[dep_id].collect(self.workbench, owner,
                                               dependencies[dep_id],
                                               container.unavailable[dep_id],
                                               container.errors[dep_id])
                except Exception:
                    container.errors[dep_id] =\
                        'An unhandled exception occured :\n%s' % format_exc()
                # Remove uncollected dependencies from the list of
                # dependencies by filtering out None values.
                dependencies[dep_id] =\
                    {k: v for k, v in dependencies[dep_id].items()
                     if v is not None}

        else:
            raise ValueError("kind argument must be 'build' or 'runtime' not :"
                             " %s" % kind)

        for dep_id in dependencies:
            if dep_id not in collectors:
                msg = 'No collector found for this kind of dependence.'
                container.errors[dep_id] = msg
                continue

            collect(dep_id)

        if dependencies:
            container.dependencies = dependencies

        container.clean()
        return container

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
        runtimes = self.run_deps_collectors.contributions
        for dep_id in dependencies:
            if dep_id not in runtimes:
                continue
            runtimes[dep_id].release(self.workbench, owner,
                                     dependencies[dep_id])
