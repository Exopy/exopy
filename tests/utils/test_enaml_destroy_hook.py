# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the add_destroy_hook class generator.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from enaml.widgets.api import Window

from exopy.utils.enaml_destroy_hook import add_destroy_hook


def test_destroy_hook():
    """Check that the ended event is emitted in destroy.

    """
    DestroyableWindow = add_destroy_hook(Window)

    assert 'd_member' in DestroyableWindow.ended.metadata

    test = DestroyableWindow()

    def observer(change):
        """Observer observing the ended event.

        """
        observer.i += 1

    observer.i = 0

    test.observe('ended', observer)
    test.destroy()
    assert observer.i == 1
