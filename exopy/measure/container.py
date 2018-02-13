# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Specialised container used to store measures.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collections import Iterable

from atom.api import Atom, List, Signal

from ..utils.container_change import ContainerChange


class MeasureContainer(Atom):
    """Generic container for measures.

    """
    #: List containing the measures. This must not be manipulated directly
    #: by user code.
    measures = List()

    #: Signal used to notify changes to the stored measures.
    changed = Signal()

    def add(self, measure, index=None):
        """Add a measure to the stored ones.

        Parameters
        ----------
        measure : Measure
            Measure to add.

        index : int | None
            Index at which to insert the measure. If None the measure is
            appended.

        """
        notification = ContainerChange(obj=self, name='measures')
        if index is None:
            index = len(self.measures)
            self.measures.append(measure)
        else:
            self.measures.insert(index, measure)

        notification.add_operation('added', (index, measure))
        self.changed(notification)

    def remove(self, measures):
        """Remove a measure or a list of measure.

        Parameters
        ----------
        measures : Measure|list[Measure]
            Measure(s) to remove.

        """
        if not isinstance(measures, Iterable):
            measures = [measures]

        notification = ContainerChange(obj=self, name='measures')
        for measure in measures:
            old = self.measures.index(measure)
            del self.measures[old]
            notification.add_operation('removed', (old, measure))

        self.changed(notification)

    def move(self, old, new):
        """Move a measure.

        Parameters
        ----------
        old : int
            Index at which the measure to move currently is.

        new_position : int
            Index at which to insert the measure.

        """
        measure = self.measures[old]
        del self.measures[old]
        self.measures.insert(new, measure)

        notification = ContainerChange(obj=self, name='measures')
        notification.add_operation('moved', (old, new, measure))
        self.changed(notification)
