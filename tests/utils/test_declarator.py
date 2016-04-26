# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of Declarator and GroupDeclarator functionalities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from future.utils import python_2_unicode_compatible

from atom.api import Bool
from enaml.core.api import Declarative

from ecpy.utils.declarator import Declarator, GroupDeclarator, import_and_get


@python_2_unicode_compatible
class DummyDeclarator(Declarator):
    """Dummy Declarator simply taking note that it registered and unregistered.

    """
    unregistered = Bool()

    def register(self, plugin, traceback):
        self.is_registered = True

    def unregister(self, plugin):
        self.unregistered = True

    def __str__(self):
        return 'Declarator'


def test_unparented_declarator_get_path():
    """Test getting the path to a declarator.

    """
    decl = Declarator()
    assert decl.get_path() is None


def test_unparented_declarator_get_group():
    """Test getting the group of an un parented declarator.

    """
    decl = Declarator()
    assert decl.get_group() is None


@pytest.fixture
def declarators():
    """Create a hierarchy of declarators.

    """
    gdecl1 = GroupDeclarator(path='foo')
    gdecl2 = GroupDeclarator(path='bar', group='int')
    gdecl1.insert_children(None, [gdecl2])
    decl = DummyDeclarator()
    gdecl2.insert_children(None, [decl])
    return (gdecl1, gdecl2, decl)


def test_group_declarator_path(declarators):
    """Test getting the path of GroupDeclarator.

    """
    assert declarators[1].get_path() == 'foo.bar'
    assert declarators[2].get_path() == 'foo.bar'


def test_group_declarator_group(declarators):
    """Test getting the group of a declarator.

    """
    assert declarators[2].get_group() == 'int'
    assert declarators[1].get_group() is None


def test_group_declarator_str(declarators):
    """Test the __str__ method.

    """
    st = str(declarators[0])
    assert 'GroupDeclarator' in st


def test_group_registering1(declarators):
    """Test group registering, unregistering.

    """
    gr, _, decl = declarators

    assert not decl.is_registered
    gr.register(None, {})
    assert decl.is_registered

    assert not decl.unregistered
    gr.unregister(None)
    assert decl.unregistered


def test_group_registering2(declarators):
    """Test group registering with path issues.

    """
    gr, _, _ = declarators

    gr.path = 'foo..'
    tb = {}
    gr.register(None, tb)

    assert 'Error 0' in tb


def test_group_registering3(declarators):
    """Test group registering with bad child.

    """
    gr, _, _ = declarators
    gr.insert_children(None, (Declarative(),))

    tb = {}
    gr.register(None, tb)

    assert 'Error 0' in tb


def test_import_and_get():
    """Test the behavior of the import and get utility function.

    """
    assert (import_and_get('ecpy.utils.declarator', 'Declarator', {}, '') is
            Declarator)

    tb = {}
    import_and_get('___ecpy', 'r', tb, 'test')
    assert 'ImportError' in tb['test']

    import_and_get('ecpy.testing.broken_enaml', 'r', tb, 'test')
    assert 'no attribute' in tb['test']

    import_and_get('ecpy.utils.declarator', '___D', tb, 'test')
    assert 'AttributeError' in tb['test']
