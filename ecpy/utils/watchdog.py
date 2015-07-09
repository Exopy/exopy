# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Collections of useful watchdog file system observers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)


class SystematicFileUpdater(FileSystemEventHandler):
    """Simple watchdog handler calling always the same function no matter the
    event

    """
    def __init__(self, handler):
        self.handler = handler

    def on_created(self, event):
        super(SystematicFileUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler()

    def on_deleted(self, event):
        super(SystematicFileUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler()

    def on_moved(self, event):
        super(SystematicFileUpdater, self).on_moved(event)
        if isinstance(event, FileMovedEvent):
            self.handler()
