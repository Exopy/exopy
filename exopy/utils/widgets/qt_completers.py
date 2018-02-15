# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Widgets with support for text completion.

"""
from atom.api import List, Tuple, Unicode, Bool, Callable, Value
from enaml.core.declarative import d_
from enaml.qt import QtCore, QtWidgets
from enaml.widgets.api import RawWidget, Feature


class QDelimitedCompleter(QtWidgets.QCompleter):
    """A custom completer to use with QtLineCompleter, QtTextEdit.

    This completer only propose completion between specified characters.

    Parameters
    ----------
    parent : QLineEdit or QTextEdit
        Widget for which to provide a completion.

    delimiters : tuple
        Tuple of length 2 specifying the characters marking the begining end
        of completion.

    entries : iterable
        Iterable of values used to propose completion.

    entries_updaters : callable
        Callable used to refresh the list of entries called once for the first
        completion after the widget gained focus.

    """
    # Signal emmitted to notify the completer it should propose a completion.
    completionNeeded = QtCore.Signal()

    def __init__(self, parent, delimiters, entries, entries_updater):

        super(QDelimitedCompleter, self).__init__(parent)

        self.delimiters = delimiters
        if isinstance(parent, QtWidgets.QLineEdit):
            self.text_getter = parent.text
            self.cursor_pos = parent.cursorPosition
            self.insert_text = parent.insert
            parent.textChanged[str].connect(self.text_changed)
            self.completionNeeded.connect(self.complete)
        elif isinstance(parent, QtWidgets.QTextEdit):
            parent.textChanged.connect(self.text_changed)
            self.cursor_pos = lambda: parent.textCursor().position()
            self.insert_text =\
                lambda text: parent.textCursor().insertText(text)
            self.text_getter = parent.toPlainText
            self.completionNeeded.connect(self._text_edit_complete)
        else:
            msg = 'Parent of QtCompleter must QLineEdit or QTextEdit, not {}'
            raise ValueError(msg.format(parent))

        self.setCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.setModel(QtCore.QStringListModel(entries, self))

        self.activated[str].connect(self.complete_text)
        self.setWidget(parent)

        self._upddate_entries = True
        self._popup_active = False
        self.entries_updater = entries_updater

    def text_changed(self, text=None):
        """Callback handling the text being edited on the parent.

        """
        if not text:
            text = self.text_getter()

        if self._upddate_entries and self.entries_updater:
            entries = self.entries_updater()
            self.setModel(QtCore.QStringListModel(entries, self))
            self._upddate_entries = False

        all_text = str(text)
        text = all_text[:self.cursor_pos()]
        split = text.split(self.delimiters[0])
        prefix = split[-1].strip()

        if len(split) > 1:
            self.setCompletionPrefix(prefix)
            self.completionNeeded.emit()
        elif self.popup().isVisible():
            self.popup().hide()

    def complete_text(self, completion):
        """When the user validate a completion add it to the text.

        """
        cursor_pos = self.cursor_pos()
        text = str(self.text_getter())
        before_text = text[:cursor_pos]
        after_text = text[cursor_pos:]
        prefix_len = len(before_text.split(self.delimiters[0])[-1].strip())

        completion = completion[prefix_len:]
        if not after_text.startswith(self.delimiters[1]):
            completion += self.delimiters[1]

        self.insert_text(completion)

    def on_focus_gained(self):
        """Mark the entries for refreshing when the widget loses focus.

        """
        self._upddate_entries = True

    def _update_entries(self, entries):
        """Update the completer completion model.

        """
        self.setModel(QtCore.QStringListModel(entries))

    def _text_edit_complete(self):
        """Propose completion for QTextEdit.

        """
        cr = self.widget().cursorRect()
        popup = self.popup()
        cr.setWidth(popup.sizeHintForColumn(0) +
                    popup.verticalScrollBar().sizeHint().width())
        self.complete(cr)


class QtLineCompleter(RawWidget):
    """Simple line editor supporting completion.

    """
    #: Text being edited by this widget.
    text = d_(Unicode())

    #: Static list of entries used to propose completion. This member value is
    #: not updated by the entries_updater.
    entries = d_(List())

    #: Callable to use to refresh the completions.
    entries_updater = d_(Callable())

    #: Delimiters marking the begining and end of completed section.
    delimiters = d_(Tuple(Unicode(), ('{', '}')))

    hug_width = 'ignore'
    features = Feature.FocusEvents

    #: Flag avoiding circular updates.
    _no_update = Bool(False)

    #: Reference to the QCompleter used by the widget.
    _completer = Value()

    # PySide requires weakrefs for using bound methods as slots.
    # PyQt doesn't, but executes unsafe code if not using weakrefs.
    __slots__ = '__weakref__'

    def create_widget(self, parent):
        """Finishes initializing by creating the underlying toolkit widget.

        """
        widget = QtWidgets.QLineEdit(parent)
        self._completer = QDelimitedCompleter(widget, self.delimiters,
                                              self.entries,
                                              self.entries_updater)
        widget.setText(self.text)
        self.proxy.widget = widget  # Anticipated so that selection works
        widget.textEdited.connect(self.update_object)
        return widget

    def update_object(self):
        """ Handles the user entering input data in the edit control.

        """
        if (not self._no_update) and self.activated:
            value = self.get_widget().text()

            self._no_update = True
            self.text = value
            self._no_update = False

    def _post_setattr_text(self, old, new):
        """Updates the editor when the object changes externally to the editor.

        """
        if (not self._no_update) and self.get_widget():
            self._no_update = True
            self.get_widget().setText(new)
            self._no_update = False

    def _post_setattr_entries(self, old, new):
        """Updates the completer entries.

        """
        if self._completer:
            self._completer._update_entries(new)

    def focus_gained(self):
        """Notify the completer the focus was lost.

        """
        self._completer.on_focus_gained()


class QCompletableTexEdit(QtWidgets.QTextEdit):
    """A QTextEdit letting the completer handles key presses when visible.

    """
    __slots__ = ('completer', )

    def keyPressEvent(self, event):
        """Overriden to let the completer handle some events when visible.

        """
        if self.completer.popup().isVisible():
            key = event.key()
            if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return,
                       QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab,
                       QtCore.Qt.Key_Backtab):
                event.ignore()
                return

        super(QCompletableTexEdit, self).keyPressEvent(event)


class QtTextCompleter(RawWidget):
    """Simple text editor supporting completion.

    """
    #: Text being edited by this widget.
    text = d_(Unicode())

    #: Static list of entries used to propose completion. This member value is
    #: not updated by the entries_updater.
    entries = d_(List())

    #: Callable to use to refresh the completions.
    entries_updater = d_(Callable())

    #: Delimiters marking the begining and end of completed section.
    delimiters = d_(Tuple(Unicode(), ('{', '}')))

    hug_width = 'ignore'
    features = Feature.FocusEvents

    #: Flag avoiding circular updates.
    _no_update = Bool(False)

    #: Reference to the QCompleter used by the widget.
    _completer = Value()

    # PySide requires weakrefs for using bound methods as slots.
    # PyQt doesn't, but executes unsafe code if not using weakrefs.
    __slots__ = '__weakref__'

    def create_widget(self, parent):
        """Finishes initializing by creating the underlying toolkit widget.

        """
        widget = QCompletableTexEdit(parent)
        self._completer = QDelimitedCompleter(widget, self.delimiters,
                                              self.entries,
                                              self.entries_updater)
        widget.completer = self._completer
        widget.setText(self.text)
        self.proxy.widget = widget  # Anticipated so that selection works
        widget.textChanged.connect(self.update_object)
        return widget

    def update_object(self):
        """ Handles the user entering input data in the edit control.

        """
        if (not self._no_update) and self.activated:
            value = self.get_widget().toPlainText()

            self._no_update = True
            self.text = value
            self._no_update = False

    def focus_gained(self):
        """Notify the completer the focus was lost.

        """
        self._completer.on_focus_gained()

    def _post_setattr_text(self, old, new):
        """Updates the editor when the object changes externally to the editor.

        """
        if (not self._no_update) and self.get_widget():
            self._no_update = True
            self.get_widget().setText(new)
            self._no_update = False

    def _post_setattr_entries(self, old, new):
        """Updates the completer entries.

        """
        if self.proxy_is_active and self._completer:
            self._completer._update_entries(new)
