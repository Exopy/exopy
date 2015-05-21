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

from atom.api import Unicode
from enaml.core.api import Declarative,  d_


class Declarator(Declarative):
    """Base class for extension object which uses a visitor pattern.

    """
    def get_path(self):
        """Query from parent the path to use for this declarator.

        Returns
        -------
        path : unicode or None
            Path declared by the parent. This can be None if no path is
            declared.

        """
        if isinstance(self.parent, GroupDeclarator):
            return self.parent.get_path()

    def get_group(self):
        """Get the group defined by the closest parent.

        """
        if not isinstance(self.parent, Declarator):
            return

        if getattr(self.parent, 'group', None):
            return self.parent.group

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
            parent_path = self.parent.get_full_path()
            if parent_path:
                paths.append(parent_path)

        if self.path:
            paths.append(self.path)

        if paths:
            return '.'.join(paths)

    def register(self, plugin, traceback):
        """Register all children Declarator.

        """
        if ':' in self.path:
            msg = 'Path cannot contain ":", issue in {} (path {}, group {})'
            traceback['Error %' % len(traceback)] = msg.format(type(self),
                                                               self.path,
                                                               self.group)
            return

        for ch in self.children:
            if not isinstance(ch, Declarator):
                msg = 'All children of GroupDeclarator must be Declarator, got'
                raise TypeError(msg + '%s' % type(ch))
            ch.register(plugin, traceback)

    def unregister(self, plugin):
        """Unregister all children Declarator.

        """
        for ch in self.children:
            if not isinstance(ch, Declarator):
                msg = 'All children of GroupDeclarator must be Declarator, got'
                raise TypeError(msg + '%s' % type(ch))
            ch.unregister(plugin)
