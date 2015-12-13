# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the ContainerChange functionalities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from pytest import raises

from ecpy.utils.container_change import ContainerChange


class TestContainerChange(object):
    """Test the ContainerChange capabilities.

    """
    def setup(self):

        self.obj = object()
        self.name = 'name'
        self.container = ContainerChange(obj=self.obj, name=self.name)

    def test_adding_moved(self):
        self.container.add_operation('moved', (1, 2, 'test'))
        assert (1, 2, 'test') in self.container.moved
        assert not self.container.added
        assert not self.container.removed
        assert not self.container.collapsed

    def test_adding_added(self):
        self.container.add_operation('added', (1, 'test'))
        assert (1, 'test') in self.container.added
        assert not self.container.moved
        assert not self.container.removed
        assert not self.container.collapsed

    def test_adding_removed(self):
        self.container.add_operation('removed', (1, 'test'))
        assert (1, 'test') in self.container.removed
        assert not self.container.added
        assert not self.container.moved
        assert not self.container.collapsed

    def test_adding_wrong_typ(self):
        with raises(ValueError):
            self.container.add_operation('test', (1, 'test'))

    def test_adding_wrong_desc(self):
        with raises(ValueError):
            self.container.add_operation('added', ('test'))
        with raises(ValueError):
            self.container.add_operation('moved', ('test'))
        with raises(ValueError):
            self.container.add_operation('removed', ('test'))

    def test_collapsing(self):
        self.container.add_operation('moved', (1, 2, 'test'))
        self.container.add_operation('added', (1, 'test'))
        self.container.add_operation('added', (2, 'aux'))

        assert self.container.collapsed
        assert not self.container.added
        assert not self.container.moved
        assert not self.container.removed

        assert len(self.container.collapsed) == 2
        assert len(self.container.collapsed[0].moved) == 1
        assert len(self.container.collapsed[1].added) == 2

        for c in self.container.collapsed:
            assert c.obj == self.obj
            assert c.name == self.name
