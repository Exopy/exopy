# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Html widget automatically scrolling ot show latest added text.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
from atom.api import Unicode
from enaml.core.declarative import d_
from enaml.qt import QtGui
from enaml.widgets.api import RawWidget


class QtAutoscrollHtml(RawWidget):
    """ Custom Html display which scrolls down to the last line on update.

    Carriage returns ('\n') are automatically converted to '<br>' so that there
    is no issue in the Html rendering.

    """
    #: Text displayed by the widget. Any Html mark up will be rendered.
    text = d_(Unicode())

    hug_width = 'ignore'
    hug_height = 'ignore'

    def create_widget(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.

        """
        widget = QtGui.QTextEdit(parent)
        widget.setReadOnly(True)
        widget.setHtml(self.text)
        return widget

    def _post_setattr_text(self, old, new):
        """ Updates the editor when the object trait changes externally to the
            editor.

        """
        if self.proxy_is_active:
            widget = self.get_widget()
            text = new.replace('\n', '<br>')
            widget.setHtml(text)
            widget.moveCursor(QtGui.QTextCursor.End)
