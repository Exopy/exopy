# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Minimal tests for the custom widgets.

"""
import pytest
import enaml

from exopy.testing.util import show_and_close_widget


@pytest.mark.ui
def test_autoscroll(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_autoscroll_html import Main
    show_and_close_widget(exopy_qtbot, Main())


@pytest.mark.ui
def test_completers(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_completers import Main
    show_and_close_widget(exopy_qtbot, Main())


@pytest.mark.ui
def test_dict_editor(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_dict_editor import Main
    show_and_close_widget(exopy_qtbot, Main())


@pytest.mark.ui
def test_dict_tree_view(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_dict_tree_view import Main
    show_and_close_widget(exopy_qtbot, Main())


@pytest.mark.ui
def test_list_str_widget(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_list_str_widget import Main
    show_and_close_widget(exopy_qtbot, Main())


@pytest.mark.ui
def test_tree_widget(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    with enaml.imports():
        from .test_tree_widget import Main
    show_and_close_widget(exopy_qtbot, Main())
