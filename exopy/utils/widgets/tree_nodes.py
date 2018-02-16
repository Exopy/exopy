# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Declarative node for tree node generation.

"""
from atom.api import (Unicode, Bool, List, Value, Property, Dict)
from enaml.core.declarative import Declarative, d_, d_func
from enaml.widgets.api import Menu


class TreeNode(Declarative):
    """Represents a tree node.

    This declaration is used to help the system determine how to extract
    informations from the underlying object to populate the node.

    Note that a Menu can be contributed as a child and will be used when
    right clicking a node. It will be passed a 'context' describing the node
    being right-clicked.

    The context will be a dictionary with the following keys :
    - 'copyable': bool, can the node be copied
    - 'cutable': bool, can the node be cut
    - 'pasteable': bool, can node be pasted here
    - 'renamable': bool, can the node be renamed
    - 'deletable': bool, can the node be deleted
    - 'not_root': bool, is the node the root node of the tree
    - 'data': tuple, (tree, TreeNode instance, object, id of the node)

    """

    #: List of object classes and/or interfaces that the node applies to
    node_for = d_(List())

    #: Either the name of a member containing a label, or a constant label, if
    #: the string starts with '='.
    label = d_(Unicode())

    #: Either the name of a member containing a tooltip, or constant tooltip,
    #: if the string starts with '='.
    tooltip = d_(Unicode())

    #: Name of the member containing children (if '', the node is a leaf).
    children_member = d_(Unicode())

    #: Name of the signal use to notify changes to the children. The payload of
    #: the signal should be a ContainerChange instance.
    children_changed = d_(Unicode())

    #: List of object classes than can be added or copied
    add = d_(List())

    #: List of object classes that can be moved
    move = d_(List())

    #: Name to use for a new instance
    name = d_(Unicode())

    #: Can the object's children be renamed?
    rename = d_(Bool(True))

    #: Can the object be renamed?
    rename_me = d_(Bool(True))

    #: Can the object's children be copied?
    copy = d_(Bool(True))

    #: Can the object's children be deleted?
    delete = d_(Bool(True))

    #: Can the object be deleted (if its parent allows it)?
    delete_me = d_(Bool(True))

    #: Can children be inserted (vs. appended)?
    insert = d_(Bool(True))

    #: Should tree nodes be automatically opened (expanded)?
    auto_open = d_(Bool(False))

    #: Automatically close sibling tree nodes?
    auto_close = d_(Bool(False))

    #: Tuple of object classes that the node applies to
    node_for_class = Property()

    #: Name of leaf item icon
    icon_item = d_(Unicode('<item>'))

    #: Name of group item icon
    icon_group = d_(Unicode('<group>'))

    #: Name of opened group item icon
    icon_open = d_(Unicode('<open>'))

    #: Resource path used to locate the node icon
    icon_path = d_(Unicode('Icon'))

    #: Selector or name for background color
    background = Value('white')

    #: Selector or name for foreground color
    foreground = Value('black')

    _py_data = Value()

    _menu = Value()

    # --- Declarative functions -----------------------------------------------

    @d_func
    def insert_child(self, obj, index, child):
        """Inserts a child into the object's children.

        """
        getattr(obj, self.children_member)[index:index] = [child]

    @d_func
    def confirm_delete(self, obj):
        """Checks whether a specified object can be deleted.

        Returns
        -------

        - **True** if the object should be deleted with no further prompting.
        - **False** if the object should not be deleted.
        - Anything else: Caller should take its default action (which might
          include prompting the user to confirm deletion).

        """
        return None

    @d_func
    def delete_child(self, obj, index):
        """Deletes a child at a specified index from the object's children.

        """
        del getattr(obj, self.children_member)[index]

    @d_func
    def move_child(self, obj, old, new):
        """Move a child of the object's children.

        """
        child = getattr(obj, self.children_member)[old]
        del getattr(obj, self.children_member)[old]
        getattr(obj, self.children_member)[new:new] = [child]

    @d_func
    def enter_rename(self, obj):
        """Start renaming an object.

        This method can be customized in case the renaming operation should not
        occur directly on the label.

        Parameters
        ----------
        obj :
            Refrence to the object the tree node being renamed is representing.

        Returns
        -------
        name : unicode
            String on which to perform the renaming.

        """
        return self.get_label(obj)

    @d_func
    def exit_rename(self, obj, label):
        """Sets the label for a specified object after a renaming operation.

        """
        label_name = self.label
        if label_name[:1] != '=':
            setattr(obj, label_name, label)

    @d_func
    def get_label(self, obj):
        """Gets the label to display for a specified object.


        """
        label = self.label
        if label[:1] == '=':
            return label[1:]

        label = getattr(obj, label)

        return label

    # =========================================================================
    # --- Initializes the object ----------------------------------------------
    # =========================================================================

    def initialize(self):
        """Collect the Menu provided as a child.

        """
        for ch in self.children:
            if isinstance(ch, Menu):
                self._menu = ch
                break

    # =========================================================================
    # --- Property Implementations --------------------------------------------
    # =========================================================================

    @node_for_class.getter
    def _get_node_for_class(self):
        return tuple([klass for klass in self.node_for])

    # =========================================================================
    # --- Overridable Methods: ------------------------------------------------
    # =========================================================================

    def allows_children(self, obj):
        """Returns whether this object can have children.

        """
        return self.children_member != ''

    def has_children(self, obj):
        """Returns whether the object has children.

        """
        return len(self.get_children(obj)) > 0

    def get_children(self, obj):
        """Gets the object's children.

        """
        return getattr(obj, self.children_member)

    def get_children_id(self, obj):
        """Gets the object's children identifier.

        """
        return self.children_member

    def append_child(self, obj, child):
        """Appends a child to the object's children.

        """
        self.insert_child(obj, len(getattr(obj, self.children_member)), child)

    def get_tooltip(self, obj):
        """Gets the tooltip to display for a specified object.

        """
        tooltip = self.tooltip
        if tooltip == '':
            return tooltip

        if tooltip[:1] == '=':
            return tooltip[1:]

        tooltip = getattr(obj, tooltip)
        if not tooltip:
            tooltip = ''

        if self.tooltip_formatter is None:
            return tooltip

        return self.tooltip_formatter(obj, tooltip)

    def get_icon(self, obj, is_expanded):
        """Returns the icon for a specified object.

        """
        if not self.allows_children(obj):
            return self.icon_item

        if is_expanded:
            return self.icon_open

        return self.icon_group

    def get_icon_path(self, obj):
        """Returns the path used to locate an object's icon.

        """
        return self.icon_path

    def get_name(self, obj):
        """Returns the name to use when adding a new object instance
        (displayed in the "New" submenu).

        """
        return self.name

    def get_menu(self, context):
        """Returns the right-click context menu for an object.

        """
        if self._menu:
            self._menu.context = context
            return self._menu
        else:
            return None

    def get_background(self, obj):
        """Returns the background color for the item.

        """
        background = self.background
        if isinstance(background, str):
            background = getattr(obj, background, background)
        return background

    def get_foreground(self, obj):
        """Returns the foreground color for the item.

        """
        foreground = self.foreground
        if isinstance(foreground, str):
            foreground = getattr(obj, foreground, foreground)
        return foreground

    def can_rename(self, obj):
        """Returns whether the object's children can be renamed.

        """
        return self.rename

    def can_rename_me(self, obj):
        """Returns whether the object can be renamed.

        """
        return self.rename_me

    def can_copy(self, obj):
        """Returns whether the object's children can be copied.

        """
        return self.copy

    def can_delete(self, obj):
        """Returns whether the object's children can be deleted.

        """
        return self.delete

    def can_delete_me(self, obj):
        """Returns whether the object can be deleted.

        """
        return self.delete_me

    def can_insert(self, obj):
        """Returns whether the object's children can be inserted (vs.
        appended).

        """
        return self.insert

    def can_auto_open(self, obj):
        """Returns whether the object's children should be automatically
        opened.

        """
        return self.auto_open

    def can_auto_close(self, obj):
        """Returns whether the object's children should be automatically
        closed.

        """
        return self.auto_close

    def is_node_for(self, obj):
        """Returns whether this is the node that handles a specified object.

        """
        return isinstance(obj, self.node_for_class)

    def can_add(self, obj, add_object):
        """Returns whether a given object is droppable on the node.

        """
        klass = self._class_for(add_object)
        if self.is_addable(klass):
            return True

        for item in self.move:
            if type(item) in (List, Dict):
                item = item[0]
            if issubclass(klass, item):
                return True

        return False

    def get_add(self, obj):
        """Returns the list of classes that can be added to the object.

        """
        return self.add

    def get_drag_object(self, obj):
        """Returns a draggable version of a specified object.

        """
        return obj

    def drop_object(self, obj, dropped_object):
        """Returns a droppable version of a specified object.

        """
        klass = self._class_for(dropped_object)
        if self.is_addable(klass):
            return dropped_object

        for item in self.move:
            if type(item) in (List, Dict):
                if issubclass(klass, item[0]):
                    return item[1](obj, dropped_object)
            elif issubclass(klass, item):
                return dropped_object

        return dropped_object

    def select(self, obj):
        """Handles an object being selected.

        """
        return True

    def is_addable(self, klass):
        """Returns whether a specified object class can be added to the node.

        """
        for item in self.add:
            if type(item) in (List, Dict):
                item = item[0]

            if issubclass(klass, item):
                return True

        return False

    def when_label_changed(self, obj, listener, remove):
        """Sets up or removes a listener for the label being changed on a
        specified object.

        """
        label = self.label
        if label[:1] != '=':
            if remove:
                obj.unobserve(label, listener)
            else:
                obj.observe(label, listener)

    def _class_for(self, obj):
        """Returns the class of an object.

        """
        if isinstance(obj, type):
            return obj

        return obj.__class__
