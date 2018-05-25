# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
from collections import Iterable

from atom.api import (Atom, List, Signal, Bool, Section, Typed)

from ...utils.atom_util import (tagged_members, member_to_pref,
                                members_from_preferences)
from ...utils.container_change import ContainerChange

#: Id used to identify dependencies type.
DEP_TYPE = 'exopy.envvar'


class EnvNode(Atom):
    """Environment variable composed of several sub env_var.

    """
    #: List of all the children of the env_var. The list should not be
    #: manipulated directly by user code.
    #: The tag 'child' is used to mark that a member can contain child env_var
    #: and is used to gather children for operation which must occur on all of
    #: them.
    children = List().tag(child=100)

    #: Signal emitted when the list of children change, the payload will be a
    #: ContainerChange instance.
    #: The tag 'child_notifier' is used to mark that a member emmit
    #: notifications about modification of another 'child' member. This allow
    #: editors to correctly track all of those.
    children_changed = Signal().tag(child_notifier='children')

    def add_child_envvar(self, index, child):
        """Add a child envvar at the given index.

        Parameters
        ----------
        index : int
            Index at which to insert the new child env_var.

        child : BaseEnvVar
            Env_var to insert in the list of children env_var.

        """
        self.children.insert(index, child)

        # In the absence of a root envvar do nothing else than inserting the
        # child.
        if self.has_root:
            child.depth = self.depth + 1
            child.path = self._child_path()

            # Give him its root so that it can proceed to any child
            # registration it needs to.
            child.parent = self
            child.root = self.root

            change = ContainerChange(obj=self, name='children',
                                     added=[(index, child)])
            self.children_changed(change)

    def move_child_envvar(self, old, new):
        """Move a child env_var.

        Parameters
        ----------
        old : int
            Index at which the child to move is currently located.

        new : BaseEnvVar
            Index at which to insert the child env_var.

        """
        child = self.children.pop(old)
        self.children.insert(new, child)

        # In the absence of a root env_var do nothing else than moving the
        # child.
        if self.has_root:

            change = ContainerChange(obj=self, name='children',
                                     moved=[(old, new, child)])
            self.children_changed(change)

    def remove_child_envvar(self, index):
        """Remove a child env_var from the children list.

        Parameters
        ----------
        index : int
            Index at which the child to remove is located.

        """
        child = self.children.pop(index)

        # Cleanup database, update preferences
        child.root = None
        child.parent = None

        change = ContainerChange(obj=self, name='children',
                                 removed=[(index, child)])
        self.children_changed(change)

    def preferences_from_members(self):
        """

        """
        prefs = super().preferences_from_members()
        for i, child in enumerate(self.children):
            prefs["child%i" % i] = child.preferences_from_members()

        return prefs

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.
            This is assembled by the EnvVarManager.

        Returns
        -------
        envvar : BaseEnvVar
            Newly created and initiliazed env_var.

        Notes
        -----
        This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.

        """
        envvar = cls()
        members_from_preferences(envvar, config)
        for name, member in tagged_members(envvar, 'child').items():

            if isinstance(member, List):
                i = 0
                pref = name + '_{}'
                validated = []
                while True:
                    child_name = pref.format(i)
                    if child_name not in config:
                        break
                    child_config = config[child_name]
                    child_class_name = child_config.pop('envvar_id')
                    child_cls = dependencies[DEP_TYPE][child_class_name]
                    child = child_cls.build_from_config(child_config,
                                                        dependencies)
                    validated.append(child)
                    i += 1

            else:
                if name not in config:
                    continue
                child_config = config[name]
                child_class_name = child_config.pop('envvar_id')
                child_class = dependencies[DEP_TYPE][child_class_name]
                validated = child_class.build_from_config(child_config,
                                                          dependencies)

            setattr(envvar, name, validated)

        return envvar
