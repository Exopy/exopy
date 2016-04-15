# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the instrument model selection widget.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml
from enaml.widgets.api import Container

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.instruments.widgets.browsing\
        import (BrowsingDialog)


def test_browsing_dialog_instruments(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to explore the instruments.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    d.show()
    process_and_sleep()

    sel = nb.pages()[0].page_widget().widgets()[0]
    sel.use_series = False
    process_app_events()
    sel.model = prof_plugin._manufacturers.manufacturers[0].instruments[0]
    process_and_sleep()

    assert type(nb.pages()[0].page_widget().widgets()[1]) is not Container


def test_browing_dialog_profiles_add(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    process_and_sleep()

    # XXX : add tests for add and edit


def test_browing_dialog_profiles_edit(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to explore the profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profiles'
    d.show()
    process_and_sleep()

    # XXX : add tests for add and edit


def test_browing_dialog_profiles_use(prof_plugin, process_and_sleep):
    """Test the browsing dialog page dedicated to follow the use of profiles.

    """
    d = BrowsingDialog(plugin=prof_plugin)
    nb = d.central_widget().widgets()[0]
    nb.selected_tab = 'profile_use'
    d.show()
    process_and_sleep()

    f = nb.pages()[-1].page_widget().widgets()[0].scroll_widget()
    assert len(f.widgets()) == 2
    p, m = prof_plugin.get_profiles('tests2', ['fp1', 'fp2'])
    process_and_sleep()
    assert len(f.widgets()) == 6
    prof_plugin.release_profiles('tests2', ['fp2'])
    process_and_sleep()
    assert len(f.widgets()) == 4
