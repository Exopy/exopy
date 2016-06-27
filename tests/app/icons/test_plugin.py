# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the icon manager plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from ecpy.testing.util import set_preferences, process_app_events
with enaml.imports():
    from .contributions import (ThemeContributor, ThemeExtensionContributor,
                                ThemeContributor2, ThemeExtensionContributor2,
                                TestIconWindow)


def test_lifecyle(app, icon_workbench, caplog):
    """Test the life cycle of the icon plugin.

    """
    icon_workbench.register(ThemeContributor())
    icon_workbench.register(ThemeExtensionContributor())

    pl = icon_workbench.get_plugin('ecpy.app.icons')
    assert pl.current_theme == 'ecpy.FontAwesome'
    assert pl.fallback_theme == 'ecpy.FontAwesome'
    assert 'dummy' in pl.icon_themes
    pl.current_theme = 'dummy'
    assert pl.get_icon('dumb1') is not None
    # Check that the extension has been registered.
    assert pl.get_icon('dumb2') is not None

    # Check we fallback on FontAwesome if the theme does not provide the
    # required icon.
    assert not caplog.records()
    assert pl.get_icon('folder-open') is not None
    assert len(caplog.records()) == 1

    # Check that requiring a non-existing icon does not crash
    assert pl.get_icon('__xxx__') is None
    assert len(caplog.records()) == 2

    # Test refreshing when new theme is registered.
    icon_workbench.register(ThemeContributor2())
    assert 'dummy2' in pl.icon_themes
    icon_workbench.unregister('dummy.icon_theme2')
    assert 'dummy2' not in pl.icon_themes

    # Test adding new contributed icons when a new extension is registered for
    # the current theme.
    icon_workbench.register(ThemeExtensionContributor2())
    assert pl.get_icon('dumb3') is not None
    icon_workbench.unregister('dummy.theme_extension2')
    assert pl.get_icon('dumb3') is None

    icon_workbench.unregister('ecpy.app.icons')


def test_overriding_preferences_if_absent(icon_workbench):
    """Test that we fall back to FontAwesome is the selected theme in the
    preferences does not exist.

    """
    set_preferences(icon_workbench, {'ecpy.app.icons': {'current_theme': '_d_',
                                                        'fallback_theme': '_f'}
                                     }
                    )
    pl = icon_workbench.get_plugin('ecpy.app.icons')
    assert pl.current_theme == pl.icon_themes[0]
    assert pl.fallback_theme == 'ecpy.FontAwesome'


def test_get_icon_handling_errors(icon_workbench, caplog):
    """Test getting an icon and handling all possible errors.

    """
    icon_workbench.register(ThemeContributor())
    icon_workbench.register(ThemeExtensionContributor())
    pl = icon_workbench.get_plugin('ecpy.app.icons')
    pl.current_theme = 'dummy'
    pl.fallback_theme = 'dummy'

    theme = pl._icon_themes.contributions['dummy']
    theme.throw = True
    assert not caplog.records()
    assert pl.get_icon('dumb1') is None
    assert len(caplog.records()) == 1
    assert 'Icon' in caplog.text()
    assert 'Fallback' in caplog.text()
    assert 'raised' in caplog.text()


def test_fontawesome(icon_workbench, windows, process_and_sleep):
    """Test getting and using a FontAwesome icon.

    """
    pl = icon_workbench.get_plugin('ecpy.app.icons')
    pl.current_theme = 'ecpy.FontAwesome'
    assert pl.get_icon('folder-open')
    w = TestIconWindow(btn_icon=pl.get_icon('folder-open'))
    w.show()
    process_app_events()
    process_and_sleep()


def test_elusiveicon(icon_workbench, windows, process_and_sleep):
    """Test getting and using an ElusiveIcon icon
    """
    pl = icon_workbench.get_plugin('ecpy.app.icons')
    pl.current_theme = 'ecpy.ElusiveIcon'
    assert pl.get_icon('folder-open')
    w = TestIconWindow(btn_icon=pl.get_icon('folder-open'))
    w.show()
    process_app_events()
    process_and_sleep()
