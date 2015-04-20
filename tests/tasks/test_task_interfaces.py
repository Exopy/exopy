# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the task interface system.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Bool, set_default

from ecpy.tasks.base_tasks import ComplexTask, RootTask
from ecpy.tasks.task_interface import InterfaceableTaskMixin, TaskInterface


class InterfaceTest(TaskInterface):
    """Base task interface for testing purposes.

    """
    #: Control falg for the check method.
    answer = Bool()

    #: Flag indicating whether or not the check method was called.
    called = Bool()

    database_entries = set_default({'itest': 1.0})

    def check(self, *args, **kwargs):
        self.called = True

        if self.answer:
            return True, {}
        else:
            return False, {'i': 0}


class InterfaceTest2(TaskInterface):
    """Subclass with a different default value for the database entry.

    """

    database_entries = set_default({'itest': 2.0})


class Mixin(InterfaceableTaskMixin, ComplexTask):
    """Complex task with interfaces.

    """

    database_entries = set_default({'test': 2.0})


class IMixin(InterfaceableTaskMixin, ComplexTask):
    """Complex task with support for interfaces but with a default behavior.

    """

    database_entries = set_default({'test': 2.0})

    def i_perform(self):
        pass


class TestInterfaceableTaskMixin(object):
    """Test the capabilities of task interfaces.

    """

    def setup(self):
        self.root = RootTask()
        self.mixin = Mixin(task_name='Simple')
        self.root.add_children_task(0, self.mixin)

    def test_interface_observer(self):
        """Test changing the interface.

        """
        i1 = InterfaceTest()
        i2 = InterfaceTest2()

        self.mixin.interface = i1
        assert i1.task is self.mixin
        assert self.mixin.database_entries == {'test': 2.0, 'itest': 1.0}

        self.mixin.interface = i2
        assert i2.task is self.mixin
        assert i1.task is None
        assert self.mixin.task_database_entries == {'test': 2.0, 'itest': 2.0}

    def test_check1(self):
        """Test running checks when the interface is present.

        """
        self.mixin.interface = InterfaceTest(answer=True)

        res, traceback = self.mixin.check()
        assert res
        assert not traceback
        assert self.mixin.interface.called

    def test_check2(self):
        """Test running checks whenno interface exist but i_perform is
        implemented.

        """
        res, traceback = IMixin().check()
        assert res
        assert not traceback

    def test_check3(self):
        """Test handling missing interface.

        """
        res, traceback = self.mixin.check()
        assert not res
        assert traceback
        assert len(traceback) == 1

    def test_check4(self):
        """Test handling a non-passing test from the interface.

        """
        self.mixin.interface = InterfaceTest()

        res, traceback = self.mixin.check()
        assert not res
        assert len(traceback) == 1
        assert self.mixin.interface.called

    def test_build_from_config1(self):
        """Test building a interfaceable task with no interface from a config.

        """
        aux = RootTask()
        aux.add_children_task(0, IMixin)
        bis = RootTask.build_from_config(aux.preferences,
                                         {'tasks': {'IMixin': IMixin,
                                                    'RootTask': RootTask}})
        assert type(bis.children[0]).__name__ == 'IMixin'

    def test_build_from_config2(self):
        """Test building a interfaceable task with no interface from a config.

        """
        self.mixin.interface = InterfaceTest(answer=True)
        bis = RootTask.build_from_config(self.root.preferences,
                                         {'tasks': {'Mixin': Mixin,
                                                    'RootTask': RootTask},
                                          'interfaces': {'InterfaceTest':
                                                         InterfaceTest}})

        assert type(bis.children[0].interface).__name__ == 'InterfaceTest'
