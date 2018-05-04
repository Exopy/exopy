# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Implementaion of the AddTaskHook hook.

"""
from enaml.workbench.api import Workbench
from atom.api import Typed, Unicode, Tuple
from .base_hooks import BasePostExecutionHook
from ...tasks.api import RootTask
from ..engines.base_engine import ExecutionInfos


class AddTasksHook(BasePostExecutionHook):
    """Post-execusion hook to add a hierarchy of tasks.

    """
    root_task = Typed(RootTask)
    workbench = Typed(Workbench)
    default_path = Unicode()
    dependencies = Tuple()

    def __init__(self, declaration, workbench):
        """ Create an empty root task

        """
        self.root_task = RootTask()
        self.workbench = workbench
        super().__init__(declaration=declaration)

    def check(self, workbench, **kwargs):
        """ Check that the post-hook task can be executed

        """
        # set the root_task default path to the one of the measure
        self.root_task.default_path = self.measurement.root_task.default_path
        res, traceback = self.root_task.check()
        return res, traceback

    def run(self, workbench, engine):
        """ Execute the post-hook task

        """
        # measure has collected the runtime dependencies given by list_runtimes
        meas_deps = self.measurement.dependencies
        runtime_deps = meas_deps.get_runtime_dependencies(self.declaration.id)
        # on the other hand, we need to collect the build dependencies
        build_deps = self.dependencies[0].dependencies
        cmd = 'exopy.app.dependencies.collect'
        core = workbench.get_plugin('enaml.workbench.core')
        deps = core.invoke_command(cmd, dict(dependencies=build_deps,
                                   kind='build'))
        if deps.errors:
            raise RuntimeError('Error when collecting the build dependencies')

        infos = ExecutionInfos(id=self.measurement.id+'.posttask',
                                task=self.root_task,
                                build_deps=deps.dependencies,
                                runtime_deps=runtime_deps,
                                observed_entries=[], # no monitor for the hooks
                                checks=not self.measurement.forced_enqueued,
                                )
        execution_result = engine.perform(infos)
        return execution_result

    def pause(self):
        """ Pause the task

        """
        self.engine.pause()

    def resume(self):
        """ Resume the task

        """
        self.engine.resume()

    def stop(self, force=False):
        """ Stop the task

        """
        self.engine.stop(force)

    def list_runtimes(self, workbench):
        """ Returns the run_time dependencies

        """
        cmd = 'exopy.app.dependencies.analyse'
        core = workbench.get_plugin('enaml.workbench.core')
        deps = core.invoke_command(cmd,
                                   {'obj': self.root_task,
                                    'dependencies': ['build', 'runtime']})
        self.dependencies = deps
        return deps[1]

    def get_state(self):
        """ Return the informations to save the post hook

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'exopy.tasks.save'
        task_prefs = core.invoke_command(cmd, {'task': self.root_task}, self)
        return task_prefs

    def set_state(self, state):
        """ Load the post hook

        """
        cmd = 'exopy.tasks.build_root'
        kwarg = {'mode': 'from config', 'config': state,
                 'build_dep': self.workbench}
        try:
            core = self.workbench.get_plugin('enaml.workbench.core')
            self.root_task = core.invoke_command(cmd, kwarg)
        except Exception:
            msg = 'Building %s, failed to restore post hook task : %s'
            errors['post hook'] = msg % (state.get('name'), format_exc())
            return None, errors
