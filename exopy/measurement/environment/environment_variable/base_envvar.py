# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------

from atom.api import (Atom, Constant, Str, Dict, Value,
                      ForwardTyped, Property)

from enaml.core.api import d_

from .infos import EnvVarInfos

from ..utils.declarator import Declarator, import_and_get


DEP_TYPE = 'exopy.envvar'


class BaseEnvVar(Atom):
    """Base class defining common members of all Environment Variables.

    This class basically defines the minimal skeleton of an Environment
    variable in term of members and methods.

    """
    #: Identifier for the build dependency collector
    dep_type = Constant(DEP_TYPE).tag(pref=True)

    #: Name of the class, used for persistence.
    envvar_id = Str().tag(pref=True)

    #: Id of the editor.
    editor_id = Str().tag(pref=True)

    #: Name of the env_var. This should be unique in hierarchy.
    name = Str().tag(pref=True)

    #: Reference to the root env_var in the hierarchy.
    root = ForwardTyped(lambda: RootEnvVar)

    #: Refrence to the parent env_var.
    parent = ForwardTyped(lambda: BaseEnvVar)

    value = Value().tag(pref=True)

    metadata = Dict().tag(pref=True)

    def preferences_from_members(self):
        """Update the entries in the preference object.

        """
        raise NotImplementedError()

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding..

        """
        raise NotImplementedError()


class EnvVar(Declarator):
    """Declarator used to contribute a env_var.

    """
    #: Path to the env_var object. Path should be dot separated and the class
    #: name preceded by ':'.
    envvar = d_(Str())

    #: Path to the view object associated with the env_var.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Str())

    #: Metadata associated to the env_var.
    metadata = d_(Dict())

    #: Id of the env_var computed from the top-level package and the env_var
    #: name
    id = Property(cached=True)

    def register(self, collector, traceback):
        """Collect env_var and view and add infos to the DeclaratorCollector
        contributions member.

        The group declared by a parent if any is taken into account. All
        Interface children are also registered.

        """
        # Build the env_var id by assembling the package name and the class
        # name
        envvar_id = self.id

        # If the env_var only specifies a name update the matching infos.
        if ':' not in self.EnvVar:
            if self.envvar not in collector.contributions:
                collector._delayed.append(self)
                return

            infos = collector.contributions[envvar_id]
            infos.metadata.update(self.metadata)

            self.is_registered = True
            return

        # Determine the path to the env_var.
        path = self.get_path()
        try:
            e_path, envvar = (path + '.' + self.envvar
                              if path else self.envvar).split(':')

        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            err_id = e_path.split('.', 1)[0] + '.' + envvar

            traceback[err_id] = msg
            return

        # Check that the env_var does not already exist.
        if envvar_id in collector.contributions or envvar_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (envvar_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(envvar, e_path)
            return

        infos = EnvVarInfos(metadata=self.metadata)

        # Get the env_var class.
        t_cls = import_and_get(e_path, envvar, traceback, envvar_id)
        if t_cls is None:
            return

        # Add group and add to collector
        infos.metadata['group'] = self.get_group()
        collector.contributions[envvar_id] = infos

        self.is_registered = True
