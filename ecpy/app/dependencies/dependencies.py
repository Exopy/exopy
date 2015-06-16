# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Extension used to declared dependencies on some objects for execution or
rebuilding of an existing structure.

Dependencies allows to collect before hand (when the full workbench is
available) as set of of objects (classes, definitions, ...) and then use it
later to in a workbench free environment to rebuild or execute some code.
Those mechanisms are used to collect task classes (build) and
also drivers classes and intsrument profiles (runtime)

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (List, Dict, Unicode)
from enaml.core.api import Declarative, d_, d_func


class BuildDependency(Declarative):
    """Build dependencies are used to rebuild ecpy structures.

    If a plugin manage objects used to build a structure that can be saved to
    a config file it should declare a BuildDependency extension and contribute
    it  to the 'build-dependencies' extensions point of the
    DependenciesPlugin (ecpy.app.dependencies).

    """
    #: Unique id for this extension.
    id = d_(Unicode())

    #: List of members names to inspect when trying to determine the build
    #: dependencies of a structure (either by inspecting the live object or
    #: a static representation such as a configuration file).
    walk_members = d_(List())

    @d_func
    def collect(self, workbench, flat_walk):
        """Collect the identified build dependencies.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        flat_walk : dict
            Dict in the format {name: set()} listing the dependencies. The key
            correspond to the walk_members declared by all BuildDependency.
            This object must not be modified in the process of collecting the
            dependencies.

        Returns
        -------
        deps : dict
            Dictionary holding the dependencies (as dictionaries) in
            categories (walk_members). If there is no dependence for a given
            category this category should be absent from the dict.

        Raises
        ------
        ValueError :
            Raised if one dependency cannot be found.

        """
        pass


class RuntimeDependency(Declarative):
    """Runtime dependencies are ressources needed at runtime by some
    structure (ex: tasks using instrument need at runtime the driver class and
    the instrument profile to work correctly).

    """
    #: Unique id for this extension.
    id = d_(Unicode())

    #: List of members names to inspect when trying to determine the runtime
    #: dependencies of a structure.
    walk_members = d_(List())

    #: Dict of name callables to call on each element of a structure when
    #: trying to determine its build dependencies
    walk_callables = d_(Dict())

    @d_func
    def collect(self, workbench, flat_walk):
        """Collect the identified runtime dependencies.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        flat_walk : dict
            Dict in the format {name: set()} listing the dependencies. The key
            correspond to the walk_members declared by all BuildDependency.
            This object must not be modified in the process of collecting the
            dependencies.

        Returns
        -------
        deps : dict
            Dictionary holding the dependencies (as dictionaries) in
            categories (walk_members). If there is no dependence for a given
            category this category should be absent from the dict.

        Raises
        ------
        ValueError :
            Raised if one dependency cannot be found.

        """
        pass
