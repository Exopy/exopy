# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base class for extension declaration relying on a visitor pattern.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import re
from importlib import import_module

from future.utils import python_2_unicode_compatible
from atom.api import Unicode, Bool
from enaml.core.api import Declarative, d_

from .traceback import format_exc


@python_2_unicode_compatible
class Declarator(Declarative):
    """Base class for extension object which uses a visitor pattern.

    """
    #: Flag indicating whether the declarator has been successfully registered
    is_registered = Bool()

    def get_path(self):
        """Query from parent the path to use for this declarator.

        Returns
        -------
        path : unicode or None
            Path declared by the parent. This can be None if no path is
            declared.

        """
        if isinstance(self.parent, Declarator):
            return self.parent.get_path()

    def get_group(self):
        """Get the group defined by the closest parent.

        """
        if not isinstance(self.parent, Declarator):
            return

        group = getattr(self.parent, 'group', None)
        if group:
            return group

        return self.parent.get_group()

    def register(self, collector, traceback):
        """Add the contribution of this extension to the plugin.

        Parameters
        ----------
        collector : DeclaratorCollector
            Collector in charge handling the registering of declarators.
            Contributions should be added to the contributions member (Dict).
            If a declarator cannot be registered because another one need to be
            registered first it should add itself to the _delayed member (List)

        traceback : dict
            Dictionary in which any issue occuring during registration should
            be recorded.

        """
        raise NotImplementedError()

    def unregister(self, plugin):
        """Remove the contribution of this extension to the plugin.

        Parameters
        ----------
        collector : DeclaratorCollector
            Collector in charge handling the registering of declarators.

        """
        raise NotImplementedError()

    def __str__(self):
        """Provide a nice string representation of the object.

        """
        raise NotImplementedError()


PATH_VALIDATOR = re.compile('^(\.?\w+)*$')


@python_2_unicode_compatible
class GroupDeclarator(Declarator):
    """Declarator used to group an ensemble of declarator.

    """
    #: Prefix path to use for all children Declarator. Path should be dot
    #: separated.
    path = d_(Unicode())

    #: Id of the group common to all children Declarator. It is the
    #: responsability of the children to mention they are part of a group.
    group = d_(Unicode())

    def get_path(self):
        """Overriden method to walk all parents.

        """
        paths = []
        if isinstance(self.parent, GroupDeclarator):
            parent_path = self.parent.get_path()
            if parent_path:
                paths.append(parent_path)

        if self.path:
            paths.append(self.path)

        if paths:
            return '.'.join(paths)

    def register(self, plugin, traceback):
        """Register all children Declarator.

        """
        if not PATH_VALIDATOR.match(self.path):
            msg = 'Invalid path {} in {} (path {}, group {})'
            traceback['Error %s' % len(traceback)] = msg.format(self.path,
                                                                type(self),
                                                                self.path,
                                                                self.group)
            return

        for ch in self.children:
            if not isinstance(ch, Declarator):
                msg = 'All children of GroupDeclarator must be Declarator, got'
                traceback['Error %s' % len(traceback)] = msg + '%s' % type(ch)
                continue
            ch.register(plugin, traceback)

        self.is_registered = True

    def unregister(self, plugin):
        """Unregister all children Declarator.

        """
        if self.is_registered:
            for ch in self.children:
                if isinstance(ch, Declarator):
                    ch.unregister(plugin)

            self.is_registered = False

    def __str__(self):
        """Identify the declarator by its path and group.

        """
        st = '{} whose path is "{}" and group is "{}" declaring :\n{}'
        return st.format(type(self).__name__, self.path, self.group,
                         '\n'.join(' - {}'.format(c) for c in self.children))


def import_and_get(path, name, traceback, id):
    """Function importing a module and retrieving an object from it.

    This function provides a common pattern for declarator.

    """
    import enaml
    try:
        with enaml.imports():
            mod = import_module(path)
    except Exception:
        msg = 'Failed to import {} :\n{}'
        traceback[id] = msg.format(path, format_exc())
        return

    try:
        return getattr(mod, name)
    except AttributeError:
        msg = '{} has no attribute {}:\n{}'
        traceback[id] = msg.format(path, name, format_exc())
        return
