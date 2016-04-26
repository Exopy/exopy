# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Minimal tests for the custom widgets.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml

from ecpy.testing.util import show_and_close_widget


@pytest.mark.ui
def test_autoscroll(windows):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_autoscroll_html import Main
    show_and_close_widget(Main())


@pytest.mark.ui
def test_completers(windows):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_completers import Main
    show_and_close_widget(Main())


@pytest.mark.ui
def test_dict_editor(windows):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_dict_editor import Main
    show_and_close_widget(Main())


@pytest.mark.ui
def test_dict_tree_view(windows):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_dict_tree_view import Main
    show_and_close_widget(Main())


@pytest.mark.ui
def test_list_str_widget(windows):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_list_str_widget import Main
    show_and_close_widget(Main())


@pytest.mark.ui
def test_tree_widget(windows):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_tree_widget import Main
    show_and_close_widget(Main())
