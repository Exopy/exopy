# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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
from enaml.qt import QtCore, QtWidgets

# cyclic notification guard flags
INDEX_GUARD = 0x1


class QtListStrWidget(RawWidget):
    """A list widget for Enaml displaying objects as strings.

    Objects that are not string should be convertible to str and hashable.

    """
    #: The list of str being viewed
    items = d_(List())

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

    # PySide requires weakrefs for using bound methods as slots.
    # PyQt doesn't, but executes unsafe code if not using weakrefs.
    __slots__ = '__weakref__'

    def initialize(self):
        """Ensures that the selected members always have meaningful values.

        """
        self._build_mapping(self.items)
        if self.items:
            self._do_default_selection()
        super(QtListStrWidget, self).initialize()

    def refresh_items(self):
        """Refresh the items displayed in the list.

        This is useful after an inplace operation on the list which is not
        notified.

        """
        self._post_setattr_items([], self.items)

    def clear_selection(self):
        """Make no item be selected.

        """
        # HINT : this only gives a visual hint to the user the selected value
        # is not updated.
        widget = self.get_widget()
        if widget is not None:
            widget.clearSelection()

    def create_widget(self, parent):
        """ Create the QListView widget.

        """
        # Create the list widget.
        widget = QtWidgets.QListWidget(parent)

        # Populate the widget.
        self._set_widget_items(widget)

        # Set the selection mode.
        if self.multiselect:
            mode = QtWidgets.QAbstractItemView.ExtendedSelection
            selected = self.selected_items
        else:
            mode = QtWidgets.QAbstractItemView.SingleSelection
            selected = [self.selected_item]
        widget.setSelectionMode(mode)

        self.proxy.widget = widget  # Anticipated so that selection works

        # Make sure the widget selection reflects the members.
        if self.items:
            self._select_on_widget(selected, widget)

        widget.itemSelectionChanged.connect(self.on_selection)
        return widget

    def on_selection(self):
        """ The signal handler for the index changed signal.

        """
        if not self._guard & INDEX_GUARD:
            self._guard ^= INDEX_GUARD
            widget = self.get_widget()
            selected = [self._rmap[index.row()]
                        for index in widget.selectedIndexes()]
            if selected:
                if self.multiselect:
                    self.selected_items = selected
                else:
                    self.selected_item = selected[0]

            self._guard ^= INDEX_GUARD

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Guard bit field.
    _guard = Int(0)

    #: Mapping between user list objects and widget list indexes.
    _map = Dict()

    #: Mapping between the widget list indexes and the user list objects.
    _rmap = Dict()

    #: String representation of the objects in the widget order.
    _items = List()

    def _post_setattr_items(self, old, new):
        """Update the widget content when the items changes.

        """
        self._build_mapping(new)
        self._set_widget_items(self.get_widget())
        if new:
            self._do_default_selection()
        else:
            if self.multiselect:
                self.selected_items = []
            else:
                self.selected_item = None

    def _post_setattr_multiselect(self, old, new):
        """Update the widget selection mode.

        """
        widget = self.get_widget()
        if widget is None:
            return

        if new:
            mode = QtWidgets.QAbstractItemView.ExtendedSelection
            if self.items:
                self.selected_items = [self.selected_item]
        else:
            mode = QtWidgets.QAbstractItemView.SingleSelection
            if self.items:
                self.selected_item = self.selected_items[0]

        widget.setSelectionMode(mode)
        if self.items:
            self._select_on_widget(self.selected_items if new
                                   else [self.selected_item])

    def _post_setattr_selected_item(self, old, new):
        """Update the widget when the selected item is changed externally.

        """
        if not self._guard & INDEX_GUARD and self.items:
            self._guard ^= INDEX_GUARD
            self._select_on_widget([new])
            self._guard ^= INDEX_GUARD

    def _post_setattr_selected_items(self, old, new):
        """Update the widget when the selected items are changed externally.

        """
        if not self._guard & INDEX_GUARD and self.items:
            self._guard ^= INDEX_GUARD
            self._select_on_widget(new)
            self._guard ^= INDEX_GUARD

    def _build_mapping(self, items):
        """Build the mapping between user objects and widget indexes.

        """
        items_map = {self.to_string(o): o for o in items}
        items = sorted(items_map) if self.sort else list(items_map)

        self._rmap = {i: items_map[item] for i, item in enumerate(items)}
        self._map = {v: k for k, v in self._rmap.items()}
        self._items = items

    def _set_widget_items(self, widget):
        """Set the list items sorting if necessary.

        """
        if widget is not None:
            widget.clearSelection()
            widget.clear()
            for i in self._items:
                widget.addItem(i)

    def _do_default_selection(self):
        """Determine the items that should be selected.

        This method also ensures that the widget state reflects the member
        values.

        """
        items = self.items
        if not self.multiselect:
            if self.selected_item not in items:
                self.selected_item = self._rmap[0]
            else:
                self._post_setattr_selected_item(None, self.selected_item)
        else:
            if not any(i in items for i in self.selected_items):
                self.selected_items = [self._rmap[0]]
            else:
                items_selected = [i for i in self.selected_items if i in items]
                if len(items_selected) == len(self.selected_item):
                    self._post_setattr_selected_items(None, items)
                else:
                    self.selected_items = items_selected

    def _select_on_widget(self, items, widget=None):
        """Select the specified items on the widget.

        """
        if widget is None:
            widget = self.get_widget()
        if widget is not None:
            widget.setCurrentItem(widget.item(0),
                                  QtCore.QItemSelectionModel.Clear)
            item_map = self._map
            for n in items:
                widget.setCurrentItem(widget.item(item_map[n]),
                                      QtCore.QItemSelectionModel.Select)
