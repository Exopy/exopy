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

from future.utils import python_2_unicode_compatible
import re

from atom.api import Unicode, Bool
from enaml.core.api import Declarative,  d_


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

    def register(self, plugin, traceback):
        """Add the contribution of this extension to the plugin.

        Parameters
        ----------
        plugin : Plugin
            Plugin to which this Declarator contribute.

        traceback : dict
            Dictionary in which any issue occuring during registration should
            be recorded.

        """
        raise NotImplementedError()

    def unregister(self, plugin):
        """Remove the contribution of this extension to the plugin.

        Parameters
        ----------
        plugin : Plugin
            Plugin to which this Declarator contribute.

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
    #: responsability of the children to mention they are part of a path.
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
