# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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

from atom.api import (Unicode)
from enaml.core.api import Declarative, d_, d_func


class BuildDependency(Declarative):
    """Build dependencies are used to rebuild exopy structures.

    If a plugin manage objects used to build a structure that can be saved to
    a config file it should declare a BuildDependency extension and contribute
    it  to the 'build-dependencies' extensions point of the
    DependenciesPlugin (exopy.app.dependencies).

    """
    #: Unique id for this extension. Should match the dep_type attribute value
    #: of the object it is meant for.
    id = d_(Unicode())

    @d_func
    def analyse(self, workbench, obj, getter, dependencies, errors):
        """Analyse the identified build dependencies and list runtime ones.

        This method should never raise an error but rather use the errors
        dictionary to signal any issue.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        obj :
            Object whose build dependencies should be analysed and runtime
            ones identified.

        getter : callable(obj, name)
            Callable to use to access obj attribute. Attribute must be accessed
            using this function rather than the usual '.' syntax as the passed
            object might be a dictionary like object.

        dependencies : set
            Set in which to list the dependencies.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        Returns
        -------
        runtime_collectors : list
            List of runtime dependencies that this object have.

        """
        raise NotImplementedError()

    @d_func
    def validate(self, workbench, dependencies, errors):
        """Validate that all the dependencies exists.

        This method is not intended to query the actual dependencies but
        simply to assert that they are theoretically available from the manager
        plugin.
        This method should never raise an error but rather use the errors
        dictionary to signal any issue.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        dependencies : set
            Set of depedencies to validate.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        raise NotImplementedError()

    @d_func
    def collect(self, workbench, dependencies, errors):
        """Collect build dependencies.

        This method should never raise an error but rather use the errors
        dictionary to signal any issue.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        dependencies : dict
            Dictionary whose values are initialised to None listing the
            dependencies to collect.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        raise NotImplementedError()


class RuntimeDependencyAnalyser(Declarative):
    """Runtime dependencies are ressources needed at runtime by some
    structure (ex: tasks using instrument need at runtime the driver class and
    the instrument profile to work correctly).

    """
    #: Unique id for this extension.
    id = d_(Unicode())

    #: Id of the collector that should be used to collect the dependencies
    #: discovered during analysis.
    collector_id = d_(Unicode())

    @d_func
    def analyse(self, workbench, obj, dependencies, errors):
        """Analyse the identified runtime dependencies of an object.

        This method should never raise an error but rather use the errors
        dictionary to signal any issue.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        obj :
            Object whose runtime dependencies should be analysed.

        dependencies : set
            Set in which to list the dependencies.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        raise NotImplementedError()


class RuntimeDependencyCollector(Declarative):
    """Runtime dependencies are ressources needed at runtime by some
    structure (ex: tasks using instrument need at runtime the driver class and
    the instrument profile to work correctly).

    """
    #: Unique id for this extension.
    id = d_(Unicode())

    @d_func
    def validate(self, workbench, dependencies, errors):
        """Validate that all the dependencies exists.

        This method should try to access the dependencies but simply assert
        that they exist.
        This method should never raise an error but rather use the errors
        dictionary to signal any issue.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        dependencies : set
            Set of depedencies to validate.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        raise NotImplementedError()

    @d_func
    def collect(self, workbench, owner, dependencies, unavailable, errors):
        """Collect the identified runtime dependencies.

        This method should never raise an error but rather use the errors
        dictionary to signal any issue.

        If some of them requires some kind of permission, this permission
        should be required.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        owner : unicode
            Calling plugin id . Used for some runtime dependencies needing to
            know the ressource owner.

        dependencies : dict
            Dictionary whose values are initialised to None listing the
            dependencies to collect.

        unavaible : set
            Set of resources that could not be provided because they are
            currently unavailable.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        raise NotImplementedError()

    @d_func
    def release(self, workbench, owner, dependencies):
        """Release resources previously collected.

        This makes sense only if the ressource requires some kind of
        permissions.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        owner : unicode
            Id of the plugin releasing the ressources.

        dependencies : iterable
            Iterable of dependencies that are no longer needed.

        """
        pass
