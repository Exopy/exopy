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

from atom.api import (Unicode)
from enaml.core.api import Declarative, d_, d_func


class BuildDependency(Declarative):
    """Build dependencies are used to rebuild ecpy structures.

    If a plugin manage objects used to build a structure that can be saved to
    a config file it should declare a BuildDependency extension and contribute
    it  to the 'build-dependencies' extensions point of the
    DependenciesPlugin (ecpy.app.dependencies).

    """
    #: Unique id for this extension. Should match the dep_type attribute value
    #: of the object it is meant for.
    id = d_(Unicode())

    @d_func
    def collect(self, workbench, obj, getter, dependencies, errors):
        """Collect the identified build dependencies and list runtime ones.

        This method should ever raise an error but rather use the errors
        dictionary to signal any issue.

        Parameters
        ----------
        workbench : enaml.workbench.api.Workbench
            Reference to the application workbench.

        obj :
            Object whose build dependencies should be collected and runtime
            ones identified.

        getter : callable(obj, name)
            Callable to use to access obj attribute. Attribute must be accessed
            using this function rather than the usual '.' syntax as the passed
            object might be a dictionary like object.

        dependencies : dict
            Dictionary in which to write the build dependencies.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        Returns
        -------
        runtime_collectors : list, optional
            List of runtime dependencies that this object have.

        """
        raise NotImplementedError()


class RuntimeDependency(Declarative):
    """Runtime dependencies are ressources needed at runtime by some
    structure (ex: tasks using instrument need at runtime the driver class and
    the instrument profile to work correctly).

    """
    #: Unique id for this extension.
    id = d_(Unicode())

    @d_func
    def collect(self, workbench, owner, obj, dependencies, unavailable,
                errors):
        """Collect the identified runtime dependencies.

        This method should ever raise an error but rather use the errors
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

        obj :
            Object whose build dependencies should be collected and runtime
            ones identified.

        dependencies : dict
            Dictionary in which to write the build dependencies.

        unavaible : set
            Set of resources that could not be provided because they are
            currently unavailable.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        raise NotImplementedError()

    @d_func
    def request(self, workbench, owner, dependencies, unavailable, errors):
        """Request the right to use the listed dependencies.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        owner : unicode
            Id of the plugin requesting the ressources.

        dependencies : dict
            Dictionary listing the dependencies to request. The values should
            be updated if necessary.

        unavaible : set
            Set of resources that could not be provided because they are
            currently unavailable.

        errors : dict
            Dictionary in which to write the errors that occured during
            collection.

        """
        pass

    @d_func
    def release(self, workbench, owner, dependencies):
        """Release resources previously acquired.

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
