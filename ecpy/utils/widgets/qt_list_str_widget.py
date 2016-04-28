# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Basic list widget limited to selection.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from future.builtins import str as ustr
from atom.api import (Bool, List, Value, Int, Callable, Dict, set_default)
from enaml.widgets.api import RawWidget
from enaml.core.declarative import d_
from enaml.qt import QtGui

# cyclic notification guard flags
INDEX_GUARD = 0x1


class QtListStrWidget(RawWidget):
    """A List widget for Enaml.

    """
    #: The list of str being viewed
    items = d_(List())

    #: The list of index of the currently selected str
    selected_index = d_(Int(0))
    selected_indexes = d_(List(Int(), [0]))

    #: The list of the currently selected str
    selected_item = d_(Value())
    selected_items = d_(List())

    #: Whether or not the user can select multiple lines
    multiselect = d_(Bool(False))

    #: Callable to use to build a unicode representation of the objects
    #: (one at a time).
    to_string = d_(Callable(ustr))

    #: Whether or not to sort the items before inserting them.
    sort = d_(Bool(True))

    hug_width = set_default(str('strong'))
    hug_height = set_default(str('ignore'))

    def refresh_items(self):
        """Refresh the items displayed in the list.

        This is useful after an inplace operation on the list which is not
        notified.

        """
        self.set_items(self.items)

    def clear_selection(self):
        """Make no item be selected.

        """
        # HINT : this only gives a visual hint to the user the selected value
        # is not updated.
        widget = self.get_widget()
        widget.clearSelection()

    def create_widget(self, parent):
        """ Create the QListView widget.

        """
        # Create the list model and accompanying controls:
        widget = QtGui.QListWidget(parent)
        self._set_items(self.items, widget)
        if self.multiselect:
            mode = QtGui.QAbstractItemView.ExtendedSelection
        else:
            mode = QtGui.QAbstractItemView.SingleSelection
        widget.setSelectionMode(mode)
        # This is necessary to ensure that the first selection is correctly
        # dispatched.
        if self.items:
            widget.setCurrentItem(widget.item(0),
                                  QtGui.QItemSelectionModel.ClearAndSelect)
        widget.itemSelectionChanged.connect(self.on_selection)
        return widget

    def on_selection(self):
        """ The signal handler for the index changed signal.

        """
        if not self._guard & INDEX_GUARD:
            self._guard ^= INDEX_GUARD
            widget = self.get_widget()
            indexes = [self._rmap[index.row()]
                       for index in widget.selectedIndexes()]
            if indexes:
                if self.multiselect:
                    self.selected_indexes = indexes
                    self.selected_items = [self.items[i] for i in indexes]
                else:
                    new_index = indexes[0]
                    self.selected_index = new_index
                    self.selected_item = self.items[new_index]

            self._guard ^= INDEX_GUARD

    def set_items(self, items):
        """Populates the widget list.

        """
        widget = self.get_widget()
        if widget is not None:
            widget.clearSelection()
            widget.clear()
        self._set_items(items, widget)

        if widget is None:
            return

        if not self.multiselect:
            if self.selected_item not in items:
                del self.selected_item
                del self.selected_index
                item = widget.item(0)
                widget.setCurrentItem(item,
                                      QtGui.QItemSelectionModel.ClearAndSelect)
            else:
                self._post_setattr_selected_item(None, self.selected_item)
        else:
            if not any(i in items for i in self.selected_items):
                del self.selected_items
                del self.selected_indexes
                item = widget.item(0)
                widget.setCurrentItem(item,
                                      QtGui.QItemSelectionModel.ClearAndSelect)
            else:
                new = [i for i in self.selected_items if i in items]
                self._post_setattr_selected_items(None, new)

    def set_multiselect(self, multiselect):
        """Set the multiselect mode.

        """
        widget = self.get_widget()
        if multiselect:
            mode = QtGui.QAbstractItemView.ExtendedSelection
        else:
            mode = QtGui.QAbstractItemView.SingleSelection

        widget.setSelectionMode(mode)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Guard bit field.
    _guard = Int(0)

    #: Mapping between user list index and widget list index
    _map = Dict()

    #: Mapping between the widget list index and the user list index
    _rmap = Dict()

    def _post_setattr_items(self, old, new):
        """Update the widget content when the items changes.

        """
        self.set_items(new)

    def _post_setattr_multiselect(self, old, new):
        """Update the widget selection mode.

        """
        self.set_multiselect(new)

    def _post_setattr_selected_index(self, old, new):
        """Update the widget when the selected index is changed externally.

        """
        if not self._guard & INDEX_GUARD and self.items:
            self._guard ^= INDEX_GUARD
            index = self._map[new]
            self.selected_item = self.items[new]
            widget = self.get_widget()
            if widget is not None:
                widget.setCurrentItem(widget.item(index),
                                      QtGui.QItemSelectionModel.ClearAndSelect)
            self._guard ^= INDEX_GUARD

    def _post_setattr_selected_indexes(self, old, new):
        """Update the widget when the selected indexes are changed externally.

        """
        if not self._guard & INDEX_GUARD and self.items:
            self._guard ^= INDEX_GUARD
            self.selected_items = [self.items[i] for i in new]
            widget = self.get_widget()
            if widget is not None:
                widget.setCurrentItem(widget.item(0),
                                      QtGui.QItemSelectionModel.Clear)
                imap = self._map
                for i in new:
                    widget.setCurrentItem(widget.item(imap[i]),
                                          QtGui.QItemSelectionModel.Select)
            self._guard ^= INDEX_GUARD

    def _post_setattr_selected_item(self, old, new):
        """Update the widget when the selected item is changed externally.

        """
        if not self._guard & INDEX_GUARD and self.items:
            self._guard ^= INDEX_GUARD
            index = self.items.index(new)
            self.selected_index = index
            widget = self.get_widget()
            if widget is not None:
                widget.setCurrentItem(widget.item(self._map[index]),
                                      QtGui.QItemSelectionModel.ClearAndSelect)
            self._guard ^= INDEX_GUARD

    def _post_setattr_selected_items(self, old, new):
        """Update the widget when the selected items are changed externally.

        """
        if not self._guard & INDEX_GUARD and self.items:
            self._guard ^= INDEX_GUARD
            indexes = [self.items.index(o) for o in new]
            self.selected_indexes = indexes
            widget = self.get_widget()
            if widget is not None:
                widget.setCurrentItem(widget.item(0),
                                      QtGui.QItemSelectionModel.Clear)
                imap = self._map
                for i in indexes:
                    widget.setCurrentItem(widget.item(imap[i]),
                                          QtGui.QItemSelectionModel.Select)
            self._guard ^= INDEX_GUARD

    def _default_selected_item(self):
        """Useful when this is accessed during initialization.

        """
        return self.items[0] if self.items else None

    def _default_selected_items(self):
        """Useful when this is accessed during initialization.

        """
        return [self.items[0]] if self.items else [None]

    def _set_items(self, items, widget):
        """Set the list items sorting if necessary.

        """
        items = [self.to_string(o) for o in items]
        s_index = list(range(len(items)))
        if self.sort:
            s_index.sort(key=items.__getitem__)

        self._rmap = {i: j for i, j in enumerate(s_index)}
        self._map = {j: i for i, j in enumerate(s_index)}
        if widget is not None:
            for i in s_index:
                widget.addItem(items[i])
