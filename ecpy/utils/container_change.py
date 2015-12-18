# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Payload to use when notifying the system about a container change.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
from atom.api import (Atom, Value, Unicode, List)


class ContainerChange(Atom):
    """Payload to use when notifying the system about a container change.

    """
    #: Reference to object from which this event originate.
    obj = Value()

    #: Name of the modified container.
    name = Unicode()

    #: List of added entries. Should not be manipulated directly by user code.
    #: Use the add_operation method to add operations.
    added = List()

    #: List of moved entries with their old and new positions. Should not be
    #: manipulated directly by user code. Use the add_operation method to add
    #: operations.
    moved = List()

    #: List of removed entries. Should not be manipulated directly by user
    #: code. Use the add_operation method to add operations.
    removed = List()

    #: List of ContainerChange representing an ordered sequence of change.
    collapsed = List()

    #: Private member used to store the last kind of added operation.
    _last_added = Value()

    def add_operation(self, typ, op_desc):
        """Add an operation.

        If two operations of different types they are represented by two
        ContainerChange added in the collapsed list. Using this method ensure
        that only one list is non empty. Consumer should always check the
        collapsed list first.

        Parameters
        ----------
        typ : {'added', 'moved', removed'}
            The type of operation to add to the change set.

        op_desc : tuple
            Tuple describing the operation it should be of the form:

            - 'added' : (index, obj)
            - 'moved' : (old_index, new_index, obj)
            - 'removed' : (index, obj)

        """
        # If we are already working with a collapsed change simply check the
        # last one to see if we can append to its changes or create a new
        # entry.
        if self.collapsed:
            if typ != self.collapsed[-1]._last_added:
                self.collapsed.append(ContainerChange(obj=self.obj,
                                                      name=self.name))

            self.collapsed[-1].add_operation(typ, op_desc)
            return

        if self._last_added and typ != self._last_added:
            # Clone ourself and clean all lists
            clone = ContainerChange(obj=self.obj, name=self.name,
                                    added=self.added,
                                    moved=self.moved, removed=self.removed,
                                    _last_added=self._last_added)
            del self.added, self.moved, self.removed
            self.collapsed.append(clone)

            # We are now in a collapsed state so add_operation will do its
            # job
            self.add_operation(typ, op_desc)
            return

        if typ not in ('moved', 'added', 'removed'):
            msg = "typ argument must be in 'moved', 'added', 'removed' not {}"
            raise ValueError(msg.format(typ))

        if typ == 'moved':
            if not len(op_desc) == 3:
                raise ValueError('Moved operation should be described by :'
                                 '(old, new, obj) not {}'.format(op_desc))
        elif typ in ('added', 'removed'):
            if not len(op_desc) == 2:
                t = typ.capitalize()
                raise ValueError(t + ' operation should be described by :'
                                 '(index, obj) not {}'.format(op_desc))

        # Otherwise simply append the operation.
        getattr(self, typ).append(op_desc)
        self._last_added = typ
