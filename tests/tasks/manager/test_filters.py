# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for base tasks filters.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest

from ecpy.tasks.api import ComplexTask, SimpleTask
from ecpy.tasks.manager.infos import TaskInfos
from ecpy.tasks.manager.filters import (TaskFilter, GroupTaskFilter,
                                        SubclassTaskFilter, MetadataTaskFilter)

@pytest.fixture
def tasks():
    pass


@pytest.fixture
def templates():
    pass


def test_task_filter(tasks, templates):
    """
    """
    pass


def test_group_task_filter(tasks, templates):
    """
    """
    pass


def test_subclass_task_filter(tasks, templates):
    """
    """
    pass


def test_meta_task_filter(tasks, templates):
    """
    """
    pass
