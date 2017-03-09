# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Implements a wrapper around the PyQt clipboard that handles Python objects
using pickle.

This has been ported from Enthought TraitsUI.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

try:
    from cPickle import dumps, load, loads, PickleError
    from cStringIO import StringIO
except ImportError:
    from pickle import dumps, load, loads, PickleError
    from io import StringIO
import warnings

from future.builtins import bytes
from enaml.qt import QtCore, QtWidgets
from atom.api import Atom, Property


class PyMimeData(QtCore.QMimeData):
    """ The PyMimeData wraps a Python instance as MIME data.

    Parameters
    ----------
    data :
        Object to copy to the clipboard.

    pickle :
        Whether or not to pickle the data.

    """
    # The MIME type for instances.
    MIME_TYPE = 'application/ecpy-qt4-instance'
    NOPICKLE_MIME_TYPE = 'application/ecpy-qt4-instance'

    def __init__(self, data=None, pickle=False):
        QtCore.QMimeData.__init__(self)

        # Keep a local reference to be returned if possible.
        self._local_instance = data

        if pickle:
            if data is not None:
                # We may not be able to pickle the data.
                try:
                    pdata = dumps(data, -1)
                    # This format (as opposed to using a single sequence)
                    # allows the type to be extracted without unpickling
                    # the data.
                    self.setData(self.MIME_TYPE, dumps(data.__class__) + pdata)
                except (PickleError, TypeError):
                    # if pickle fails, still try to create a draggable
                    warnings.warn(("Could not pickle dragged object %s, " +
                                   "using %s mimetype instead") % (repr(data),
                                  self.NOPICKLE_MIME_TYPE), RuntimeWarning)
                    self.setData(self.NOPICKLE_MIME_TYPE,
                                 str(id(data)).encode('utf8'))

        else:
            self.setData(self.NOPICKLE_MIME_TYPE, str(id(data)).encode('utf8'))

    @classmethod
    def coerce(cls, md):
        """ Wrap a QMimeData or a python object to a PyMimeData.

        """
        # See if the data is already of the right type.  If it is then we know
        # we are in the same process.
        if isinstance(md, cls):
            return md

        if isinstance(md, PyMimeData):
            # If it is a PyMimeData, migrate all its data, subclasses should
            # override this method if it doesn't do things correctly for them
            data = md.instance()
            nmd = cls()
            nmd._local_instance = data
            for format in md.formats():
                nmd.setData(format, md.data(format))

        elif isinstance(md, QtCore.QMimeData):
            # If it is a QMimeData, migrate all its data
            nmd = cls()
            for format in md.formats():
                nmd.setData(format, md.data(format))

        else:
            # By default, don't try to pickle the coerced object
            pickle = False

            # See if the data is a list, if so check for any items which are
            # themselves of the right type.  If so, extract the instance and
            # track whether we should pickle.
            # HINT lists should suffice for now, but may want other containers
            if isinstance(md, list):
                md = [item.instance() if isinstance(item, PyMimeData) else item
                      for item in md]

            # Arbitrary python object, wrap it into PyMimeData
            nmd = cls(md, pickle)

        return nmd

    def instance(self):
        """ Return the instance.

        """
        if self._local_instance is not None:
            return self._local_instance

        if not self.hasFormat(self.MIME_TYPE):
            # We have no pickled python data defined.
            return None

        io = StringIO(bytes(self.data(self.MIME_TYPE)))

        try:
            # Skip the type.
            load(io)

            # Recreate the instance.
            return load(io)
        except PickleError:
            pass

        return None

    def instance_type(self):
        """ Return the type of the instance.

        """
        if self._local_instance is not None:
            return self._local_instance.__class__

        try:
            if self.hasFormat(self.MIME_TYPE):
                return loads(bytes(self.data(self.MIME_TYPE)))
        except PickleError:
            pass

        return None

    def local_paths(self):
        """ The list of local paths from url list, if any.

        """
        ret = []
        for url in self.urls():
            if url.scheme() == 'file':
                ret.append(url.toLocalFile())
        return ret


class _Clipboard(Atom):
    """ The _Clipboard class provides a wrapper around the PyQt clipboard.

    """
    # --- Members definitions -------------------------------------------------

    #: The instance on the clipboard (if any).
    instance = Property()

    #: Set if the clipboard contains an instance.
    has_instance = Property()

    #: The type of the instance on the clipboard (if any).
    instance_type = Property()

    # --- Instance property methods -------------------------------------------

    @instance.getter
    def _instance_getter(self):
        """ The instance getter.

        """
        md = PyMimeData.coerce(QtWidgets.QApplication.clipboard().mimeData())
        if md is None:
            return None

        return md.instance()

    @instance.setter
    def _instance_setter(self, data):
        """ The instance setter.

        """
        QtWidgets.QApplication.clipboard().setMimeData(PyMimeData(data))

    @has_instance.getter
    def _has_instance_getter(self):
        """ The has_instance getter.

        """
        clipboard = QtWidgets.QApplication.clipboard()
        return clipboard.mimeData().hasFormat(PyMimeData.MIME_TYPE)

    @instance_type.getter
    def _instance_type_getter(self):
        """ The instance_type getter.

        """
        md = PyMimeData.coerce(QtWidgets.QApplication.clipboard().mimeData())
        if md is None:
            return None

        return md.instance_type()

#  The singleton clipboard instance.
CLIPBOARD = _Clipboard()
