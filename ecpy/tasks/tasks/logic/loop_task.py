# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task allowing to perform a loop. The iterable is given by an interface.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Typed, Bool, set_default)

from timeit import default_timer

from ...base_tasks import (SimpleTask, ComplexTask)
from ...task_interface import InterfaceableTaskMixin
from ...tools.decorators import handle_stop_pause
from .loop_exceptions import BreakException, ContinueException


class LoopTask(InterfaceableTaskMixin, ComplexTask):
    """Complex task which, at each iteration, call all its child tasks.

    """
    #: Class attribute marking this task as being part of the logical tasks
    logic_task = True

    #: Flag indicating whether or not to time the loop.
    timing = Bool().tag(pref=True)

    #: Task to call before other child tasks with current loop value. This task
    #: is simply a convenience and can be set to None.
    task = Typed(SimpleTask).tag(child=50)

    database_entries = set_default({'point_number': 11, 'index': 1,
                                    'value': 0})

    def check(self, *args, **kwargs):
        """Overriden so that interface check are run before children ones.

        """
        test = True
        traceback = {}
        if self.interface:
            i_test, i_traceback = self.interface.check(*args, **kwargs)

            traceback.update(i_traceback)
            test &= i_test

        c_test, c_traceback = super(LoopTask, self).check(*args, **kwargs)

        traceback.update(c_traceback)
        test &= c_test

        return test, traceback

    def perform_loop(self, iterable):
        """Perform the loop on the iterable calling all child tasks at each
        iteration.

        This method shoulf be called by the interface at the appropriate time.

        Parameters
        ----------
        iterable : iterable
            Iterable on which the loop should be performed.

        """
        if self.timing:
            if self.task:
                self._perform_loop_timing_task(iterable)
            else:
                self._perform_loop_timing(iterable)
        else:
            if self.task:
                self._perform_loop_task(iterable)
            else:
                self._perform_loop(iterable)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _perform_loop(self, iterable):
        """Perform the loop when there is no child and timing is not required.

        """
        self.write_in_database('point_number', len(iterable))

        root = self.root
        for i, value in enumerate(iterable):

            if handle_stop_pause(root):
                return

            self.write_in_database('index', i+1)
            self.write_in_database('value', value)
            try:
                for child in self.children:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue

    def _perform_loop_task(self, iterable):
        """Perform the loop when there is a child and timing is not required.

        """
        self.write_in_database('point_number', len(iterable))

        root = self.root
        for i, value in enumerate(iterable):

            if handle_stop_pause(root):
                return

            self.write_in_database('index', i+1)
            self.task.perform_(self.task, value)
            try:
                for child in self.children:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue

    def _perform_loop_timing(self, iterable):
        """Perform the loop when there is no child and timing is required.

        """
        self.write_in_database('point_number', len(iterable))

        root = self.root
        for i, value in enumerate(iterable):

            if handle_stop_pause(root):
                return

            self.write_in_database('index', i+1)
            self.write_in_database('value', value)
            tic = default_timer()
            try:
                for child in self.children:
                    child.perform_(child)
            except BreakException:
                self.write_in_database('elapsed_time', default_timer()-tic)
                break
            except ContinueException:
                self.write_in_database('elapsed_time', default_timer()-tic)
                continue
            self.write_in_database('elapsed_time', default_timer()-tic)

    def _perform_loop_timing_task(self, iterable):
        """Perform the loop when there is a child and timing is required.

        """
        self.write_in_database('point_number', len(iterable))

        root = self.root
        for i, value in enumerate(iterable):

            if handle_stop_pause(root):
                return

            self.write_in_database('index', i+1)
            tic = default_timer()
            self.task.perform_(self.task, value)
            try:
                for child in self.children:
                    child.perform_(child)
            except BreakException:
                self.write_in_database('elapsed_time', default_timer()-tic)
                break
            except ContinueException:
                self.write_in_database('elapsed_time', default_timer()-tic)
                continue
            self.write_in_database('elapsed_time', default_timer()-tic)

    def _post_setattr_task(self, old, new):
        """Keep the database entries in sync with the task member.

        """
        if old:
            if self.has_root:
                old.unregister_from_database()
                old.root = None
                old.parent = None

        if new:
            if self.has_root:
                new.depth = self.depth + 1
                new.database = self.database
                new.path = self._child_path()

                # Give him its root so that it can proceed to any child
                # registration it needs to.
                new.parent = self
                new.root = self.root

                # Ask the child to register in database
                new.register_in_database()

            aux = self.database_entries.copy()
            if 'value' in aux:
                del aux['value']
            self.database_entries = aux

        else:
            aux = self.database_entries.copy()
            aux['value'] = 1.0
            self.database_entries = aux

        if self.has_root:
            self.register_preferences()

    def _post_setattr_timing(self, old, new):
        """Keep the database entries in sync with the timing flag.

        """
        if new:
            aux = self.database_entries.copy()
            aux['elapsed_time'] = 1.0
            self.database_entries = aux
        else:
            aux = self.database_entries.copy()
            if 'elapsed_time' in aux:
                del aux['elapsed_time']
            self.database_entries = aux
