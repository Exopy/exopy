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

import pytest

from atom.api import Bool, Unicode, set_default

from ecpy.tasks.base_tasks import ComplexTask, RootTask
from ecpy.tasks.task_interface import (InterfaceableTaskMixin, TaskInterface,
                                       InterfaceableInterfaceMixin, IInterface)


class InterfaceTest(TaskInterface):
    """Base task interface for testing purposes.

    """
    #: Control flag for the check method.
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

    def perform(self):
        self.task.write_in_database('itest', 2.0)


class InterfaceTest2(TaskInterface):
    """Subclass with a different default value for the database entry.

    """
    #: Member to test auto formatting of tagged members.
    fmt = Unicode().tag(fmt=True)

    #: Member to test auto evaluation of tagged members.
    feval = Unicode().tag(feval=True)

    database_entries = set_default({'fmt': '', 'feval': 0, 'itest': 2.0})


class InterfaceTest3(InterfaceableInterfaceMixin, TaskInterface):
    """Interfaceable interface

    """

    database_entries = set_default({'test': 2.0})


class InterfaceTest4(InterfaceableInterfaceMixin, TaskInterface):
    """Interfaceable interface with default interface.

    """

    database_entries = set_default({'test': 2.0})

    def i_perform(self):
        self.task.write_in_database('test', 3.0)


class IIinterfaceTest1(IInterface):
    """Base IInterface for testing.

    """
    #: Control flag for the check method.
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

    def perform(self):
        self.task.write_in_database('itest', 2.0)


class IIinterfaceTest2(IInterface):
    """Base IInterface for testing.

    """
    #: Member to test auto formatting of tagged members.
    fmt = Unicode().tag(fmt=True)

    #: Member to test auto evaluation of tagged members.
    feval = Unicode().tag(feval=True)

    database_entries = set_default({'fmt': '', 'feval': 0, 'itest': 2.0})


class Mixin(InterfaceableTaskMixin, ComplexTask):
    """Complex task with interfaces.

    """

    database_entries = set_default({'test': 2.0})


class IMixin(InterfaceableTaskMixin, ComplexTask):
    """Complex task with support for interfaces but with a default behavior.

    """

    database_entries = set_default({'test': 2.0})

    def i_perform(self):
        self.write_in_database('test', 3.0)


class TestInterfaceableTaskMixin(object):
    """Test the capabilities of task interfaces.

    """

    def setup(self):
        self.root = RootTask()
        self.mixin = Mixin(name='Simple')
        self.root.add_child_task(0, self.mixin)

    def test_interface_observer(self):
        """Test changing the interface.

        """
        i1 = InterfaceTest()
        i2 = InterfaceTest2()

        self.mixin.interface = i1
        assert i1.task is self.mixin
        assert self.mixin.database_entries == {'test': 2.0, 'itest': 1.0}
        assert i1.interface_class[1] == (self.mixin.task_class,)

        self.mixin.interface = i2
        assert i2.task is self.mixin
        assert i1.task is None
        assert self.mixin.database_entries == {'test': 2.0, 'itest': 2.0,
                                               'fmt': '', 'feval': 0}

    def test_check1(self):
        """Test running checks when the interface is present.

        """
        self.mixin.interface = InterfaceTest(answer=True)

        res, traceback = self.mixin.check()
        assert res
        assert not traceback
        assert self.mixin.interface.called

    def test_check2(self):
        """Test running checks when no interface exist but i_perform is
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
        assert 'root/Simple-interface' in traceback

    def test_check4(self):
        """Test handling a non-passing test from the interface.

        """
        self.mixin.interface = InterfaceTest()

        res, traceback = self.mixin.check()
        assert not res
        assert len(traceback) == 1
        assert self.mixin.interface.called

    def test_check5(self):
        """Check that auto-check of fmt and feavl tagged members works.

        """
        self.mixin.interface = InterfaceTest2(fmt='{Simple_test}',
                                              feval='2*{Simple_test}')

        res, traceback = self.mixin.check()
        assert res
        assert not traceback
        assert self.root.get_from_database('Simple_fmt') == '2.0'
        assert self.root.get_from_database('Simple_feval') == 4.0

    def test_check6(self):
        """Check that auto-check of fmt and feavl handle errors.

        """
        self.mixin.interface = InterfaceTest2(fmt='{Simple_test*}',
                                              feval='2*{Simple_test}*')

        res, traceback = self.mixin.check()
        assert not res
        assert self.root.get_from_database('Simple_fmt') == ''
        assert self.root.get_from_database('Simple_feval') == 0
        assert len(traceback) == 2
        assert 'root/Simple-fmt' in traceback
        assert 'root/Simple-feval' in traceback

    def test_perform1(self):
        """Test perform does call interface if present.

        """
        self.mixin.interface = InterfaceTest()
        self.root.database.prepare_for_running()

        self.mixin.perform()
        assert self.mixin.get_from_database('Simple_itest') == 2.0

    def test_perform2(self):
        """Test perform use i_perform when no interface exists.

        """
        self.root.remove_child_task(0)
        self.mixin = IMixin(name='Simple')
        self.root.add_child_task(0, self.mixin)
        self.root.database.prepare_for_running()

        self.mixin.perform()
        assert self.root.get_from_database('Simple_test') == 3.0

    def test_build_from_config1(self):
        """Test building a interfaceable task with no interface from a config.

        """
        aux = RootTask()
        aux.add_child_task(0, IMixin())

        bis = RootTask.build_from_config(aux.preferences,
                                         {'ecpy.task': {'IMixin': IMixin,
                                                        'RootTask': RootTask}})
        assert type(bis.children[0]).__name__ == 'IMixin'

    def test_build_from_config2(self):
        """Test building a interfaceable task with an interface from a config.

        """
        self.mixin.interface = InterfaceTest(answer=True)
        self.root.update_preferences_from_members()
        deps = {'ecpy.task': {'Mixin': Mixin, 'RootTask': RootTask},
                'ecpy.tasks.interface':
                    {('InterfaceTest', ('Mixin',)): InterfaceTest}}
        bis = RootTask.build_from_config(self.root.preferences, deps)

        assert type(bis.children[0].interface).__name__ == 'InterfaceTest'

    def test_traverse(self):
        """Test traversing a task with interface.

        """
        self.mixin.interface = InterfaceTest2()

        w = list(self.mixin.traverse())
        assert w == [self.mixin, self.mixin.interface]


class TestInterfaceableInterfaceMixin(object):
    """Test the capabilities of task interfaces.

    """

    def setup(self):
        self.root = RootTask()
        self.mixin = InterfaceTest3()
        self.root.add_child_task(0, Mixin(name='Simple', interface=self.mixin))

    def test_interface_observer(self):
        """Test changing the interface.

        """
        i1 = IIinterfaceTest1()
        i2 = IIinterfaceTest2()

        self.mixin.interface = i1
        assert i1.parent is self.mixin
        assert i1.task is self.mixin.task
        assert i1.interface_class[1] ==\
            (self.mixin.interface_class[1] + (self.mixin.interface_class[0],))
        assert self.mixin.task.database_entries == {'test': 2.0, 'itest': 1.0}

        self.mixin.interface = i2
        assert i2.task is self.mixin.task
        assert i1.parent is None
        with pytest.raises(AttributeError):
            i1.task
        assert self.mixin.task.database_entries == {'test': 2.0, 'itest': 2.0,
                                                    'fmt': '', 'feval': 0}

    def test_check1(self):
        """Test running checks when the interface is present.

        """
        self.mixin.interface = IIinterfaceTest1(answer=True)

        res, traceback = self.mixin.check()
        assert res
        assert not traceback
        assert self.mixin.interface.called

    def test_check2(self):
        """Test running checks when no interface exist but i_perform is
        implemented.

        """
        interface = InterfaceTest4()
        self.root.children[0].interface = interface
        res, traceback = interface.check()
        assert res
        assert not traceback

    def test_check3(self):
        """Test handling missing interface.

        """
        res, traceback = self.mixin.check()
        assert not res
        assert traceback
        assert len(traceback) == 1
        assert 'root/Simple/InterfaceTest3-interface' in traceback

    def test_check4(self):
        """Test handling a non-passing test from the interface.

        """
        self.mixin.interface = IIinterfaceTest1()

        res, traceback = self.mixin.check()
        assert not res
        assert len(traceback) == 1
        assert self.mixin.interface.called

    def test_check5(self):
        """Check that auto-check of fmt and feavl tagged members works.

        """
        self.mixin.interface = IIinterfaceTest2(fmt='{Simple_test}',
                                                feval='2*{Simple_test}')

        res, traceback = self.mixin.check()
        assert res
        assert not traceback
        assert self.root.get_from_database('Simple_fmt') == '2.0'
        assert self.root.get_from_database('Simple_feval') == 4.0

    def test_check6(self):
        """Check that auto-check of fmt and feavl handle errors.

        """
        self.mixin.interface = IIinterfaceTest2(fmt='{Simple_test*}',
                                                feval='2*{Simple_test}*')

        res, traceback = self.mixin.check()
        print(traceback)
        assert not res
        assert self.root.get_from_database('Simple_fmt') == ''
        assert self.root.get_from_database('Simple_feval') == 0
        assert len(traceback) == 2
        assert 'root/Simple-fmt' in traceback
        assert 'root/Simple-feval' in traceback

    def test_perform1(self):
        """Test perform does call interface if present.

        """
        self.mixin.interface = IIinterfaceTest1()
        self.root.database.prepare_for_running()

        self.mixin.perform()
        assert self.root.get_from_database('Simple_itest') == 2.0

    def test_perform2(self):
        """Test perform use i_perform when no interface exists.

        """
        self.mixin = InterfaceTest4()
        self.root.children[0].interface = self.mixin
        self.root.database.prepare_for_running()

        self.mixin.perform()
        assert self.root.get_from_database('Simple_test') == 3.0

    def test_build_from_config1(self):
        """Test building a interfaceable interface with no interface from a
        config.

        """
        aux = RootTask()
        mixin = Mixin()
        mixin.interface = InterfaceTest3()
        aux.add_child_task(0, mixin)
        deps = {'ecpy.task': {'Mixin': Mixin, 'RootTask': RootTask},
                'ecpy.tasks.interface':
                    {('InterfaceTest3', ('Mixin',)): InterfaceTest3}}
        bis = RootTask.build_from_config(aux.preferences, deps)
        assert type(bis.children[0].interface).__name__ == 'InterfaceTest3'

    def test_build_from_config2(self):
        """Test building a interfaceable interface with an interface from a
        config.

        """
        self.mixin.interface = IIinterfaceTest1(answer=True)
        self.root.update_preferences_from_members()
        deps = {'ecpy.task': {'Mixin': Mixin, 'RootTask': RootTask},
                'ecpy.tasks.interface':
                    {('InterfaceTest3', ('Mixin',)): InterfaceTest3,
                     ('IIinterfaceTest1',
                      ('Mixin', 'InterfaceTest3')): IIinterfaceTest1
                     }
                }
        bis = RootTask.build_from_config(self.root.preferences, deps)

        interface = bis.children[0].interface.interface
        assert type(interface).__name__ == 'IIinterfaceTest1'
        assert self.root.children[0].database_entries ==\
            {'test': 2.0, 'itest': 1.0}

    def test_traverse(self):
        """Test traversing a task with an interfaceable interface.

        """
        class Test(InterfaceableInterfaceMixin, IIinterfaceTest2):
            pass

        iaux = IIinterfaceTest1()
        self.mixin.interface = Test()
        self.mixin.interface.interface = iaux

        task = self.root.children[0]
        w = list(task.traverse())
        assert w == [task, self.mixin, self.mixin.interface, iaux]

        w = list(task.traverse(1))
        assert w == [task, self.mixin, self.mixin.interface]
