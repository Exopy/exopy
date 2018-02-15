# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the base settings.

"""
from exopy.instruments.settings.base_settings import BaseSettings, Settings


def test_base_settings():
    """Test the base settings functions.

    """
    s = BaseSettings(user_id='Dummy', declaration=Settings(id='test'))
    del s.title
    assert s.title == 'Dummy (test)'
    s.user_id = 'D'
    assert s.title == 'D (test)'
    assert 'id' in s.gather_infos()
