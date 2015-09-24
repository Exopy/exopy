# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the DestroyHook mixin class..

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.utils.enaml_destroy_hook import DestroyHook


def test_destroy_hook():
    """Check that the ended event is emitted in destroy.

    """
    assert 'd_member' in DestroyHook.ended.metadata

    test = DestroyHook()

    def observer(change):
        """Observer observing the ended event.

        """
        observer.i += 1

    observer.i = 0

    test.observe('ended', observer)
    test.destroy()
    assert observer.i == 1
