# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the database used fo tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from pytest import raises

from ecpy.tasks.tools.database import TaskDatabase

# TODO add tests checking that the notifiers did run properly
# =============================================================================
# --- Edition mode tests ------------------------------------------------------
# =============================================================================


def test_database_nodes():
    """Test all nodes operations.

    """
    database = TaskDatabase()
    database.create_node('root', 'node1')
    database.create_node('root/node1', 'node2')
    database.rename_node('root', 'node1', 'n_node1')
    database.delete_node('root/n_node1', 'node2')
    with raises(KeyError):
        database.delete_node('root/n_node1', 'node2')


def test_database_values():
    """Test get/set value operations.

    """
    database = TaskDatabase()
    assert database.set_value('root', 'val1', 1) is True
    assert database.get_value('root', 'val1') == 1
    assert database.set_value('root', 'val1', 2) is False
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    assert database.get_value('root/node1', 'val2') == 'a'
    assert database.get_value('root/node1', 'val1') == 2
    with raises(KeyError):
        database.get_value('root/rrtt', 'val')
    with raises(KeyError):
        database.get_value('root/node1/rr', 'val')


def test_database_delete_value():
    """Test delete value operation.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    assert database.get_value('root', 'val1') == 1
    database.delete_value('root', 'val1')
    with raises(KeyError):
        database.get_value('root', 'val1')
    with raises(KeyError):
        database.delete_value('root', 'val1')


def test_database_values3():
    """Test accessing a value with the wrong path.

    """
    database = TaskDatabase()
    database.create_node('root', 'node1')
    database.create_node('root/node1', 'node2')
    database.set_value('root/node1/node2', 'val1', 1)
    assert database.get_value('root/node1/node2', 'val1') == 1
    with raises(KeyError):
        database.get_value('root/node1', 'val1')


def test_renaming_values():
    """Test renaming values to which no access exs is linked.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.rename_values('root', ['val1'], ['new_val'])
    with raises(KeyError):
        database.get_value('root', 'val1')
    assert database.get_value('root', 'new_val') == 1

    with raises(KeyError):
        database.rename_values('root', ['val1'], ['new_val'])


def test_database_listing():
    """Test database entries listing.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')

    assert database.list_all_entries() == \
        sorted(['root/val1', 'root/node1/val2'])
    assert database.list_all_entries(values=True) == \
        {'root/val1': 1, 'root/node1/val2': 'a'}
    assert database.list_accessible_entries('root') == ['val1']
    assert database.list_accessible_entries('root/node1') ==\
        sorted(['val1', 'val2'])

    # Test excluding values from the database.
    database.excluded = ['val1']
    assert database.list_all_entries() == sorted(['root/node1/val2'])
    assert database.list_all_entries(values=True) == {'root/node1/val2': 'a'}
    assert database.list_accessible_entries('root') == []
    assert database.list_accessible_entries('root/node1') == sorted(['val2'])


def test_access_exceptions():
    """Test access exceptions.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    database.create_node('root', 'node2')
    database.set_value('root/node2', 'val3', 2.0)

    assert database.list_accessible_entries('root') == ['val1']

    database.add_access_exception('root', 'root/node1', 'val2')
    assert database.list_accessible_entries('root') == ['val1', 'val2']
    assert database.get_value('root', 'val2') == 'a'

    database.add_access_exception('root', 'root/node2', 'val3')
    assert database.list_accessible_entries('root') == ['val1', 'val2', 'val3']
    assert database.get_value('root', 'val3') == 2.0

    database.remove_access_exception('root', 'val2')
    assert database.list_accessible_entries('root') == ['val1', 'val3']

    database.remove_access_exception('root')
    assert database.list_accessible_entries('root') == ['val1']


def test_access_exceptions_renaming_values():
    """Test renaming values linked to an access ex.

    """
    database = TaskDatabase()
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val1', 2.0)

    database.add_access_exception('root', 'root/node1', 'val1')
    database.rename_values('root/node1', ['val1'], ['new_val'], {'val1': 1})
    assert database.get_value('root', 'new_val') == 2.0


def test_access_exceptions_renaming_node():
    """Test renaming a node holding an access exception.

    The relative path is exactly the name of the renamed node.

    """
    database = TaskDatabase()
    database.create_node('root', 'node1')
    database.create_node('root/node1', 'node2')
    database.set_value('root/node1/node2', 'val1', 2.0)

    database.add_access_exception('root/node1', 'root/node1/node2', 'val1')
    assert database.get_value('root/node1', 'val1') == 2.0

    database.rename_node('root/node1', 'node2', 'node22')
    assert database.get_value('root/node1', 'val1') == 2.0

    database.rename_node('root', 'node1', 'node11')
    assert database.get_value('root/node11', 'val1') == 2.0


def test_copy_node_values():
    """Test copying the values found in a node.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    database.create_node('root', 'node2')
    database.set_value('root/node2', 'val3', 2.0)

    assert database.copy_node_values() == {'val1': 1}
    assert database.copy_node_values('root/node1') == {'val2': 'a'}


def test_list_nodes():
    """Test listing the nodes existing in the database.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    database.create_node('root', 'node2')
    database.set_value('root/node2', 'val3', 2.0)

    nodes = database.list_nodes()
    assert 'root' in nodes
    assert 'root/node1' in nodes
    assert 'root/node2' in nodes


# =============================================================================
# --- Running mode tests ------------------------------------------------------
# =============================================================================

def test_forbidden_operations():
    """Check that all forbidden operations does raise a RuntimeError.

    """
    database = TaskDatabase()
    database.prepare_to_run()
    with raises(RuntimeError):
        database.rename_values('root', [], [])
    with raises(RuntimeError):
        database.delete_value('root', '')
    with raises(RuntimeError):
        database.create_node('root', '')
    with raises(RuntimeError):
        database.rename_node('root', '', '')
    with raises(RuntimeError):
        database.delete_node('root', '')


def test_flattening_database():
    """Check that the database can be flattened.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')

    database.prepare_to_run()


def test_index_op_on_flat_database1():
    """Test operation on flat database relying on indexes.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    database.create_node('root/node1', 'node2')

    database.prepare_to_run()
    assert database.get_entries_indexes('root', ['val1']) == {'val1': 0}
    assert database.get_entries_indexes('root/node1', ['val1', 'val2']) == \
        {'val1': 0, 'val2': 1}
    assert database.get_entries_indexes('root/node1/node2', ['val2']) == \
        {'val2': 1}

    assert database.get_values_by_index([0, 1]) == [1, 'a']
    assert database.get_values_by_index([0, 1], 'e_') == \
        {'e_0': 1, 'e_1': 'a'}
    with raises(KeyError):
        database.get_entries_indexes('root/rr', [''])


def test_index_op_on_flat_database2():
    """Test operation on flat database relying on indexes when a simple access
    ex exists.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    database.add_access_exception('root', 'root/node1', 'val2')

    database.prepare_to_run()
    assert database.get_entries_indexes('root', ['val1']) == {'val1': 0}
    assert database.get_entries_indexes('root', ['val1', 'val2']) == \
        {'val1': 0, 'val2': 1}


def test_index_op_on_flat_database3():
    """Test operation on flat database relying on indexes when a nested access
    ex exists.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.create_node('root/node1', 'node2')
    database.set_value('root/node1/node2', 'val2', 'a')
    database.add_access_exception('root/node1', 'root/node1/node2', 'val2')
    database.add_access_exception('root', 'root/node1', 'val2')

    database.prepare_to_run()
    assert database.get_entries_indexes('root', ['val1']) == {'val1': 0}
    assert database.get_entries_indexes('root', ['val1', 'val2']) == \
        {'val1': 0, 'val2': 1}


def test_get_set_on_flat_database1():
    """Test get/set operations on flat database using names.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')

    database.prepare_to_run()
    assert not database.set_value('root', 'val1', 2)
    assert database.get_value('root', 'val1') == 2
    assert database.get_value('root/node1', 'val1') == 2


def test_get_set_on_flat_database2():
    """Test get/set operations on flat database using names when an access ex
    exists.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    database.add_access_exception('root', 'root/node1', 'val2')

    database.prepare_to_run()
    assert not database.set_value('root', 'val2', 2)
    assert database.get_value('root', 'val2') == 2


def test_get_set_on_flat_database3():
    """Test get/set operations on flat database using names when a nested
    access ex exists.

    """
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.create_node('root/node1', 'node2')
    database.set_value('root/node1/node2', 'val2', 'a')
    database.add_access_exception('root/node1', 'root/node1/node2', 'val2')
    database.add_access_exception('root', 'root/node1', 'val2')

    database.prepare_to_run()
    assert not database.set_value('root', 'val2', 2)
    assert database.get_value('root', 'val2') == 2

    assert not database.set_value('root/node1', 'val2', 2)
    assert database.get_value('root/node1', 'val2') == 2
