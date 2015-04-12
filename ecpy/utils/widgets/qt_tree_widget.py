# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tree widget for enaml.

This tree widget has limited functionality, it supports only :
- single selection
- single column tree
- no undo capabilities
- single TreeNode fitting an object.


It should be used with the TreeNode declartive class and the Menu item given
in qt_tree_menu.enaml.

This is vastly inspired from TraitsUI implementation.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import copy
import os
from past.builtins import basestring
from future.builtins import str as unicode
from atom.api import (Bool, List, Value, Dict, Int)

from enaml.widgets.api import RawWidget
from enaml.core.declarative import d_
from enaml.qt import QtCore, QtGui

from .qt_clipboard import CLIPBOARD, PyMimeData
from .tree_nodes import TreeNode


def pixmap_cache(name, path=None):
    """ Return the QPixmap corresponding to a filename. If the filename does
    not contain a path component, 'path' is used (or if 'path' is not
    specified, the local 'images' directory is used).

    """
    name_path, name = os.path.split(name)
    name = name.replace(' ', '_').lower()
    if name_path:
        filename = os.path.join(name_path, name)
    else:
        if path is None:
            filename = os.path.join(os.path.dirname(__file__), 'images', name)
        else:
            filename = os.path.join(path, name)
    filename = os.path.abspath(filename)

    pm = QtGui.QPixmap()
    if not QtGui.QPixmapCache.find(filename, pm):
        pm.load(filename)
        QtGui.QPixmapCache.insert(filename, pm)
    return pm


#: Cyclic notification guard flags
INDEX_GUARD = 0x1

#: Standard icons map.
STD_ICON_MAP = {
    '<item>':   QtGui.QStyle.SP_FileIcon,
    '<group>':  QtGui.QStyle.SP_DirClosedIcon,
    '<open>':   QtGui.QStyle.SP_DirOpenIcon
    }


class QtTreeWidget(RawWidget):
    """Simple style of tree editor.

    """
    # --- Members definitions -------------------------------------------------

    #: Root object of the tree.
    root_node = d_(Value())

    #: Is the tree editor is scrollable? This value overrides the default.
    scrollable = d_(Bool(True))

    #: The currently selected object
    selected_item = d_(Value())

    #: Flag to hide the root node of the tree.
    hide_root = d_(Bool())

    #: Flag controlling the automatic expansion of nodes.
    auto_expand = d_(Bool(True))

    #: Whether or not to show the icons for the leaves and nodes.
    show_icons = d_(Bool(True))

    #: Nodes declared by the user as children of this widget.
    nodes = List()

    hug_height = 'ignore'

    #: Cyclic selection notification guard.
    _guard = Int()

    #: Object id to object map used internally.
    _map = Dict()

    # --- Enaml Raw widget interface ------------------------------------------

    def create_widget(self, parent):
        """Finishes initializing the editor by creating the underlying toolkit
        widget.

        """
        # Create tree widget and connect signal
        tree = _TreeWidget(parent)
        tree._controller = self

        # Hide the header as we have a single column.
        tree.setHeaderHidden(True)

        self.nodes = [ch for ch in self.children if isinstance(ch, TreeNode)]

        tree.itemExpanded.connect(self._on_item_expanded)
        tree.itemCollapsed.connect(self._on_item_collapsed)
        tree.itemSelectionChanged.connect(self._on_tree_sel_changed)
        tree.customContextMenuRequested.connect(self._on_context_menu)
        tree.itemChanged.connect(self._on_nid_changed)

        self._set_root_node(self.root_node, tree)
        # The proxy is not yet active so we must set the selected item manually
        self._guard ^= INDEX_GUARD
        self.selected_item = self.root_node
        self._guard ^= INDEX_GUARD
        return tree

    def destroy(self):
        """ Disposes of the contents of an editor.

        """
        tree = self.get_widget()
        if tree is not None:
            # Stop the chatter (specifically about the changing selection).
            tree.blockSignals(True)

            self._delete_node(tree.invisibleRootItem())

        super(QtTreeWidget, self).destroy()

    # --- Public API ----------------------------------------------------------

    def get_object(self, nid):
        """Gets the object associated with a specified node.

        """
        return self._get_node_data(nid)[2]

    def get_parent(self, obj, name=''):
        """Returns the object that is the immmediate parent of a specified
        object in the tree.

        """
        nid = self._get_object_nid(obj, name)
        if nid is not None:
            pnid = nid.parent()
            if pnid is not self.get_widget().invisibleRootItem():
                return self.get_object(pnid)
        return None

    def get_node(self, obj, name=''):
        """Returns the node associated with a specified object.

        """
        nid = self._get_object_nid(obj, name)
        if nid is not None:
            return self._get_node_data(nid)[1]
        return None

    # --- Observers -----------------------------------------------------------

    def _post_setattr_selected_item(self, old, new):
        """Update the selection when it changes externally.

        """
        if not self._guard & INDEX_GUARD:
            self._guard ^= INDEX_GUARD
            try:
                tree = self.get_widget()
                tree.setCurrentItem(self._object_info(new)[2])
            except Exception:
                self._guard ^= INDEX_GUARD
                raise

    def _post_setattr_root_node(self, old, new):
        if self.proxy_is_active:
            self._set_root_node(new)

    # --- Node manipulation methods -------------------------------------------

    def _expand_levels(self, nid, levels, expand=True):
        """Expands from the specified node the specified number of sub-levels.

        """
        if levels > 0:
            expanded, node, obj = self._get_node_data(nid)
            if self._has_children(node, obj):
                self._expand_node(nid)
                if expand:
                    nid.setExpanded(True)
                for cnid in self._nodes_for(nid):
                    self._expand_levels(cnid, levels - 1)

    def _set_root_node(self, model, tree=None):
        """Set the root node of the tree.

        """
        if not tree:
            tree = self.get_widget()
        tree.clear()

        self._map = {}

        obj, node = self._node_for(model)
        if node is not None:
            if self.hide_root:
                nid = tree.invisibleRootItem()
            else:
                nid = self._create_item(tree, node, obj)

            self._map[id(obj)] = [(node.get_children_id(obj), nid)]
            self._add_listeners(node, obj)
            self._set_node_data(nid, (False, node, obj))
            if self.hide_root or self._has_children(node, obj):
                self._expand_node(nid)
                if not self.hide_root:
                    nid.setExpanded(True)
                    tree.setCurrentItem(nid)
            self._expand_levels(nid, self.auto_expand, False)

        ncolumns = tree.columnCount()
        if ncolumns > 1:
            for i in range(ncolumns):
                tree.resizeColumnToContents(i)

        tree.setCurrentItem(tree.topLevelItem(0))

    def _create_item(self, nid, node, obj, index=None):
        """Create  a new TreeWidgetItem as per word_wrap policy.

        Index is the index of the new node in the parent:
        None implies append the child to the end.

        """
        if index is None:
            cnid = QtGui.QTreeWidgetItem(nid)
        else:
            cnid = QtGui.QTreeWidgetItem()
            nid.insertChild(index, cnid)

        cnid.setText(0, node.get_label(obj))
        cnid.setIcon(0, self._get_icon(node, obj))
        cnid.setToolTip(0, node.get_tooltip(obj))

        color = node.get_background(obj)
        if color:
            cnid.setBackground(0, self._get_brush(color))
        color = node.get_foreground(obj)
        if color:
            cnid.setForeground(0, self._get_brush(color))

        return cnid

    def _set_label(self, nid, text):
        """ Set the label of the specified item.

        """
        expanded, node, obj = self._get_node_data(nid)
        nid.setText(0, node.get_label(obj))

    def _append_node(self, nid, node, obj):
        """ Appends a new node to the specified node.
        """
        return self._insert_node(nid, None, node, obj)

    def _insert_node(self, nid, index, node, obj):
        """ Inserts a new node before a specified index into the children of
        the specified node.

        """

        cnid = self._create_item(nid, node, obj, index)

        has_children = self._has_children(node, obj)
        self._set_node_data(cnid, (False, node, obj))
        self._map.setdefault(id(obj), []).append((node.get_children_id(obj),
                                                  cnid))
        self._add_listeners(node, obj)

        # Automatically expand the new node (if requested):
        if node.allows_children(obj):
            if has_children and node.can_auto_open(obj):
                cnid.setExpanded(True)
            else:
                # Qt only draws the control that expands the tree if there is a
                # child.  As the tree is being populated lazily we create a
                # dummy that will be removed when the node is expanded for the
                # first time.
                cnid._dummy = QtGui.QTreeWidgetItem(cnid)

        # Return the newly created node:
        return cnid

    def _delete_node(self, nid):
        """ Deletes a specified tree node and all its children.

        """
        for cnid in self._nodes_for(nid):
            self._delete_node(cnid)

        # See if it is a dummy.
        pnid = nid.parent()
        if pnid is not None and getattr(pnid, '_dummy', None) is nid:
            pnid.removeChild(nid)
            del pnid._dummy
            return

        try:
            expanded, node, obj = self._get_node_data(nid)
        except AttributeError:
            # The node has already been deleted.
            pass
        else:
            id_object = id(obj)
            object_info = self._map[id_object]
            for i, info in enumerate(object_info):
                # QTreeWidgetItem does not have an equal operator, so use id()
                if id(nid) == id(info[1]):
                    del object_info[i]
                    break

            if len(object_info) == 0:
                self._remove_listeners(node, obj)
                del self._map[id_object]

        if pnid is None and self.proxy_is_active:
            tree = self.get_widget()
            tree.takeTopLevelItem(tree.indexOfTopLevelItem(nid))
        else:
            pnid.removeChild(nid)

    def _expand_node(self, nid):
        """ Expands the contents of a specified node (if required).

        """
        expanded, node, obj = self._get_node_data(nid)

        # Lazily populate the item's children:
        if not expanded:
            # Remove any dummy node.
            dummy = getattr(nid, '_dummy', None)
            if dummy is not None:
                nid.removeChild(dummy)
                del nid._dummy

            for child in node.get_children(obj):
                child, child_node = self._node_for(child)
                if child_node is not None:
                    self._append_node(nid, child_node, child)

            # Indicate the item is now populated:
            self._set_node_data(nid, (True, node, obj))

    def _nodes_for(self, nid):
        """ Returns all child node ids of a specified node id.

        """
        return [nid.child(i) for i in range(nid.childCount())]

    def _node_index(self, nid):
        """Return the index of a specified node id within its parent.

        """
        pnid = nid.parent()
        if pnid is None:
            if self.hide_root and self.proxy_is_active:
                pnid = self.get_widget().invisibleRootItem()
            if pnid is None:
                return (None, None, None)

        for i in range(pnid.childCount()):
            if pnid.child(i) is nid:
                _, pnode, pobject = self._get_node_data(pnid)
                return (pnode, pobject, i)
        else:
            # doesn't match any node, so return None
            return (None, None, None)

    def _has_children(self, node, obj):
        """ Returns whether a specified object has any children.

        """
        return (node.allows_children(obj) and node.has_children(obj))

    def _get_icon(self, node, obj, is_expanded=False):
        """ Returns the index of the specified object icon.

        """
        if True:
            return QtGui.QIcon()

        icon_name = node.get_icon(obj, is_expanded)
        if isinstance(icon_name, basestring):
            icon = STD_ICON_MAP.get(icon_name)

            if icon is not None and self.proxy_is_active:
                return self.get_widget().style().standardIcon(icon)

            path = node.get_icon_path(obj)
            if isinstance(path, basestring):
                path = [path, node]
            else:
                path.append(node)
            # resource_manager.locate_image( icon_name, path )
            reference = None
            if reference is None:
                return QtGui.QIcon()
            file_name = reference.filename
        else:
            # Assume it is an ImageResource, and get its file name directly:
            file_name = icon_name.absolute_path

        return QtGui.QIcon(pixmap_cache(file_name))

    def _add_listeners(self, node, obj):
        """Adds the event listeners for a specified object.

        """
        if node.allows_children(obj):
            obj.observe(node.children_member, self._children_replaced)
            obj.observe(node.children_changed, self._children_updated)

        node.when_label_changed(obj, self._label_updated, False)

    def _remove_listeners(self, node, obj):
        """Removes any event listeners from a specified object.

        """
        if node.allows_children(obj):
            obj.unobserve(node.children_member, self._children_replaced)
            obj.unobserve(node.children_changed, self._children_updated)

        node.when_label_changed(obj, self._label_updated, True)

    # --- Object instrospection -----------------------------------------------

    def _object_info(self, obj, name=''):
        """Tree node data for an object in the form (expanded, node, nid).

        """
        info = self._map[id(obj)]
        for name2, nid in info:
            if name == name2:
                break
        else:
            nid = info[0][1]

        expanded, node, ignore = self._get_node_data(nid)

        return (expanded, node, nid)

    def _object_info_for(self, obj, name=''):
        """Returns the tree node data for a specified object as a list of the
        form: [ (expanded, node, nid), ... ].

        """
        result = []
        for name2, nid in self._map[id(obj)]:
            if name == name2:
                expanded, node, ignore = self._get_node_data(nid)
                result.append((expanded, node, nid))

        return result

    def _node_for(self, obj):
        """Returns the TreeNode associated with a specified object.

        """
        if ((type(obj) is tuple) and (len(obj) == 2) and
                isinstance(obj[1], TreeNode)):
            return obj

        # Select all nodes which understand this object:
        nodes = [node for node in self.nodes
                 if node.is_node_for(obj)]
        # If only one found, we're done, return it:
        if len(nodes) == 1:
            return (obj, nodes[0])

        # If none found, give up:
        if len(nodes) == 0:
            return (obj, None)

    def _node_for_class(self, klass):
        """Returns the TreeNode associated with a specified class.

        """
        for node in self.nodes:
            if issubclass(klass, tuple(node.node_for)):
                return node
        return None

    def _node_for_class_name(self, class_name):
        """Returns the node and class associated with a specified class name.

        """
        for node in self.nodes:
            for klass in node.node_for:
                if class_name == klass.__name__:
                    return (node, klass)
        return (None, None)

    def _get_object_nid(self, obj, name=''):
        """Gets the ID associated with a specified object (if any).

        """
        info = self._map.get(id(obj))
        if info is None:
            return None
        for name2, nid in info:
            if name == name2:
                return nid
        else:
            return info[0][1]

    @staticmethod
    def _get_node_data(nid):
        """Gets the node specific data. """
        return nid._py_data

    @staticmethod
    def _set_node_data(nid, data):
        """Sets the node specific data. """
        nid._py_data = data

    # --- Object operations ---------------------------------------------------

    def _append(self, node, obj, data, make_copy=False):
        """Performs an append operation.

        """
        if make_copy:
            data = copy.deepcopy(data)
        node.append_child(obj, data)

    def _insert(self, node, obj, index, data, make_copy=False):
        """Performs an insert operation.

        """
        if make_copy:
            data = copy.deepcopy(data)
        node.insert_child(obj, index, data)

    def _delete(self, node, obj, index):
        """Performs an delete operation.

        """
        node.delete_child(obj, index)

    def _move(self, node, obj, old, new):
        """Performs a move operation.

        """
        node.move_child(obj, old, new)

    # --- Tree event handlers -------------------------------------------------

    def _on_item_expanded(self, nid):
        """ Handles a tree node being expanded.

        """
        expanded, node, obj = self._get_node_data(nid)

        # If 'auto_close' requested for this node type, close all of the node's
        # siblings:
        if node.can_auto_close(obj):
            parent = nid.parent()

            if parent is not None:
                for snid in self._nodes_for(parent):
                    if snid is not nid:
                        snid.setExpanded(False)

        # Expand the node (i.e. populate its children if they are not there
        # yet):
        self._expand_node(nid)

        self._update_icon(nid)

    def _on_item_collapsed(self, nid):
        """ Handles a tree node being collapsed.

        """
        self._update_icon(nid)

    def _on_tree_sel_changed(self):
        """ Handles a tree node being selected.

        """
        if self.proxy_is_active and not self._guard & INDEX_GUARD:
            # Get the new selection:
            nids = self.get_widget().selectedItems()

            selected = []
            if len(nids) > 0:
                for nid in nids:
                    # If there is a real selection, get the associated object:
                    expanded, node, sel_object = self._get_node_data(nid)
                    selected.append(sel_object)

                    # Try to inform the node specific handler of the selection,
                    # if there are multiple selections, we only care about the
                    # first

                    # QTreeWidgetItem does not have an equal operator, so use
                    # id()
                    if id(nid) == id(nids[0]):
                        obj = sel_object
                        # not_handled = node.select(sel_object)
            else:
                nid = None
                obj = None
                # not_handled = True

            # Set the value of the new selection:
            self._guard ^= INDEX_GUARD
            self.selected_item = obj
            self._guard ^= INDEX_GUARD

    def _on_context_menu(self, pos):
        """ Handles the user requesting a context menuright clicking on a tree
        node.

        """
        tree = self.get_widget()
        nid = tree.itemAt(pos)

        if nid is None:
            return

        _, node, obj = self._get_node_data(nid)

        # Try to get the parent node of the node clicked on:
        pnid = nid.parent()
        if pnid is None or pnid is tree.invisibleRootItem():
            parent_node = parent_object = None
        else:
            _, parent_node, parent_object = self._get_node_data(pnid)

        context = {'copyable': self._is_copyable(obj, node, parent_node),
                   'cutable': self._is_cutable(obj, node, parent_node),
                   'pasteable': self._is_pasteable(obj, node, parent_node),
                   'renamable': self._is_renameable(obj, node, parent_node),
                   'deletable': self._is_deletable(obj, node, parent_node),
                   'not_root': parent_node is not None,
                   'data': (self, node, obj, nid)}

        menu = node.get_menu(context)
        if menu is not None:
            if not all((not action.visible or action.separator)
                       for action in menu.items()):
                # Use the menu specified by the node:
                menu.popup()

    # -------------------------------------------------------------------------
    #  Menu action helper methods:
    # -------------------------------------------------------------------------

    def _is_copyable(self, obj, node, parent_node):
        return ((parent_node is not None) and parent_node.can_copy(obj))

    def _is_cutable(self, obj, node, parent_node):
        can_cut = ((parent_node is not None) and
                   parent_node.can_copy(obj) and
                   parent_node.can_delete(obj))
        return (can_cut and node.can_delete_me(obj))

    def _is_pasteable(self, obj, node, parent_node):
        return node.can_add(obj, CLIPBOARD.instance_type)

    def _is_deletable(self, obj, node, parent_node):
        can_delete = ((parent_node is not None) and
                      parent_node.can_delete(obj))
        return (can_delete and node.can_delete_me(obj))

    def _is_renameable(self, obj, node, parent_node):
        can_rename = ((parent_node is not None) and
                      parent_node.can_rename(obj))

        can_rename = (can_rename and node.can_rename_me(obj))

        # Set the widget item's editable flag appropriately.
        nid = self._get_object_nid(obj)
        flags = nid.flags()
        if can_rename:
            flags |= QtCore.Qt.ItemIsEditable
        else:
            flags &= ~QtCore.Qt.ItemIsEditable
        nid.setFlags(flags)

        return can_rename

    def _is_droppable(self, node, obj, add_object, for_insert):
        """ Returns whether a given object is droppable on the node.

        """
        if for_insert and (not node.can_insert(obj)):
            return False

        return node.can_add(obj, add_object)

    def _drop_object(self, node, obj, dropped_object, make_copy=True):
        """ Returns a droppable version of a specified object.

        """
        new_object = node.drop_object(obj, dropped_object)
        if (new_object is not dropped_object) or (not make_copy):
            return new_object

        return copy.deepcopy(new_object)

    def _on_nid_changed(self, nid, col):
        """Handle changes to a widget item subsequent to a renaming operation.

        """
        # The node data may not have been set up for the nid yet.  Ignore it if
        # it hasn't.
        try:
            _, node, obj = self._get_node_data(nid)
        except Exception:
            return

        new_label = unicode(nid.text(col))
        old_label = node.get_label(obj)

        if new_label != old_label:
            if new_label != '':
                node.exit_rename(obj, new_label)
            else:
                self._set_label(nid, old_label)

    def _children_replaced(self, change):
        """ Handles the children of a node being completely replaced.

        """
        obj = change['object']
        name = change['name']

        for expanded, node, nid in self._object_info_for(obj, name):
            children = node.get_children(obj)

            # Only add/remove the changes if the node has already been expanded
            if expanded:
                # Delete all current child nodes:
                for cnid in self._nodes_for(nid):
                    self._delete_node(cnid)

                # Add all of the children back in as new nodes:
                for child in children:
                    child, child_node = self._node_for(child)
                    if child_node is not None:
                        self._append_node(nid, child_node, child)

            # Try to expand the node (if requested):
            if node.can_auto_open(obj):
                nid.setExpanded(True)

    def _children_updated(self, change):
        """ Handles the children of a node being changed.

        """
        obj = change.obj
        name = change.name

        if change.collapsed:
            for ch in change.collapsed:
                self._children_updated(ch)

        elif change.added:
            for expanded, node, nid in self._object_info_for(obj, name):

                # Only add the changes if the node has already been expanded
                if expanded:

                    # Add all of the children that were added:
                    for index, child in change.added:
                        child, child_node = self._node_for(child)
                        if child_node is not None:
                            self._insert_node(nid, index, child_node,
                                              child)

                # Try to expand the node (if requested):
                if node.can_auto_open(obj):
                    nid.setExpanded(True)

        elif change.removed:
            for expanded, node, nid in self._object_info_for(obj, name):

                # Only remove the changes if the node has already been expanded
                if expanded:
                    # Remove all of the children that were deleted:
                    nodes = self._nodes_for(nid)
                    for i in [ind for ind, _ in change.removed]:
                        self._delete_node(nodes[i])

                # Try to expand the node (if requested):
                if node.can_auto_open(obj):
                    nid.setExpanded(True)

        elif change.moved:
            for expanded, node, nid in self._object_info_for(obj, name):

                # Only move nodes if the parent has already been expanded
                if expanded:
                    for old, new, child in change.moved:
                        # Remove all of the children that were deleted:
                        self._delete_node(self._nodes_for(nid)[old])

                        child, child_node = self._node_for(child)
                        if child_node is not None:
                            self._insert_node(nid, new, child_node,
                                              child)

                # Try to expand the node (if requested):
                if node.can_auto_open(obj):
                    nid.setExpanded(True)

    def _label_updated(self, change):
        """  Handles the label of an object being changed.

        """
        if self.proxy_is_active:
            tree = self.get_widget()
            obj = change['object']
            # Prevent the itemChanged() signal from being emitted.
            blk = tree.blockSignals(True)

            nids = {}
            for name2, nid in self._map[id(obj)]:
                if nid not in nids:
                    nids[nid] = None
                    node = self._get_node_data(nid)[1]
                    self._set_label(nid, node.get_label(obj))
                    self._update_icon(nid)

            tree.blockSignals(blk)

    # --- Miscellaneous methods -----------------------------------------------

    def _get_brush(self, color):
        """Get brush associated to a color.

        """
        if isinstance(color, list) or isinstance(color, tuple):
            q_color = QtGui.QColor(*color)
        else:
            q_color = QtGui.QColor(color)
        return QtGui.QBrush(q_color)

    def _update_icon(self, nid):
        """ Updates the icon for a specified node.

        """
        expanded, node, obj = self._get_node_data(nid)
        nid.setIcon(0, self._get_icon(node, obj, expanded))


class _TreeWidget(QtGui.QTreeWidget):
    """ The _TreeWidget class is a specialised QTreeWidget that reimplements
        the drag'n'drop support so that it hooks into the provided support.

    """

    def __init__(self, parent):
        """ Initialise the tree widget.
        """
        QtGui.QTreeWidget.__init__(self, parent)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)

        self._dragging = None
        self._controller = None

    def resizeEvent(self, event):
        """ Overridden to emit sizeHintChanged() of items for word wrapping """
        super(self.__class__, self).resizeEvent(event)

    def startDrag(self, actions):
        """ Reimplemented to start the drag of a tree widget item.

        """
        nid = self.currentItem()
        if nid is None:
            return

        self._dragging = nid

        _, node, obj = self._controller._get_node_data(nid)

        # Convert the item being dragged to MIME data.
        drag_object = node.get_drag_object(obj)
        md = PyMimeData.coerce(drag_object)

        # Render the item being dragged as a pixmap.
        nid_rect = self.visualItemRect(nid)
        rect = nid_rect.intersected(self.viewport().rect())
        pm = QtGui.QPixmap(rect.size())
        pm.fill(self.palette().base().color())
        painter = QtGui.QPainter(pm)

        option = self.viewOptions()
        option.state |= QtGui.QStyle.State_Selected
        option.rect = QtCore.QRect(nid_rect.topLeft() -
                                   rect.topLeft(), nid_rect.size())
        self.itemDelegate().paint(painter, option, self.indexFromItem(nid))

        painter.end()

        # Calculate the hotspot so that the pixmap appears on top of the
        # original item.
        hspos = self.viewport().mapFromGlobal(QtGui.QCursor.pos()) - \
            nid_rect.topLeft()

        # Start the drag.
        drag = QtGui.QDrag(self)
        drag.setMimeData(md)
        drag.setPixmap(pm)
        drag.setHotSpot(hspos)
        drag.exec_(actions)

    def dragEnterEvent(self, e):
        """ Reimplemented to see if the current drag can be handled by the
            tree.

        """
        # Assume the drag is invalid.
        e.ignore()

        # Check if we have a python object instance, we might be interested
        data = PyMimeData.coerce(e.mimeData()).instance()
        if data is None:
            return

        # We might be able to handle it (but it depends on what the final
        # target is).
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        """ Reimplemented to see if the current drag can be handled by the
            particular tree widget item underneath the cursor.

        """
        # Assume the drag is invalid.
        e.ignore()
        action, to_node, to_object, to_index, data = self._get_action(e)

        if action is not None:
            e.acceptProposedAction()

    def dropEvent(self, e):
        """ Reimplemented to update the model and tree.

        """
        # Assume the drop is invalid.
        e.ignore()
        control = self._controller

        dragging = self._dragging
        self._dragging = None

        action, to_node, to_object, to_index, data = self._get_action(e)
        if action == 'move' and dragging is not None:
            data = control._drop_object(to_node, to_object, data, False)
            if data is not None:
                _, _, from_index = control._node_index(dragging)
                control._move(to_node, to_object, from_index, to_index)

        elif action == 'append':
            if dragging is not None:
                data = control._drop_object(to_node, to_object, data, False)
                if data is not None:
                    control._delete(*control._node_index(dragging))
                    control._append(to_node, to_object, data, False)
            else:
                data = control._drop_object(to_node, to_object, data, True)
                if data is not None:
                    control._append(to_node, to_object, data, False)

        elif action == 'insert':
            if dragging is not None:
                data = control._drop_object(to_node, to_object, data, False)
                if data is not None:
                    from_node, from_object, from_index = \
                        control._node_index(dragging)
                    if ((to_object is from_object) and
                            (to_index > from_index)):
                        to_index -= 1
                    control._delete(from_node, from_object,
                                    from_index)
                    control._insert(to_node, to_object, to_index,
                                    data, False)
            else:
                data = control._drop_object(to_node, to_object, data, True)
                if data is not None:
                    control._insert(to_node, to_object, to_index,
                                    data, False)
        else:
            return
        self.viewport().update()
        e.acceptProposedAction()

    def _get_action(self, event):
        """ Work out what action on what object to perform for a drop event.

        """
        # default values to return
        action = None
        to_node = None
        to_object = None
        to_index = None
        data = None

        control = self._controller

        # Get the tree widget item under the cursor.
        nid = self.itemAt(event.pos())
        if nid is None:
            if control.hide_root:
                nid = self.invisibleRootItem()
            else:
                return (action, to_node, to_object, to_index, data)

        # Check that the target is not the source of a child of the source.
        if self._dragging is not None:
            pnid = nid
            while pnid is not None:
                if pnid is self._dragging:
                    return (action, to_node, to_object, to_index, data)

                pnid = pnid.parent()

        data = PyMimeData.coerce(event.mimeData()).instance()
        _, node, obj = control._get_node_data(nid)

        if event.proposedAction() == QtCore.Qt.MoveAction and \
                control._is_droppable(node, obj, data, False):
            # append to node being dropped on
            action = 'append'
            to_node = node
            to_object = obj
            to_index = None
        else:
            # get parent of node being dropped on
            to_node, to_object, to_index = control._node_index(nid)
            if to_node is None:
                # no parent, can't do anything
                action = None
            elif control._is_droppable(to_node, to_object, data, True):
                if to_object is control.get_parent(data):
                    action = 'move'
                # insert into the parent of the node being dropped on
                else:
                    action = 'insert'
            elif control._is_droppable(to_node, to_object, data, False):
                # append to the parent of the node being dropped on
                action = 'append'
            else:
                # parent can't be modified, can't do anything
                action = None

        return (action, to_node, to_object, to_index, data)
