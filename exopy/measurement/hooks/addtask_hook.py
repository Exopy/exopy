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

from atom.api import Typed, Unicode, Tuple
from .base_hooks import BasePostExecutionHook
from ...tasks.api import RootTask
from ..engines.base_engine import ExecutionInfos


# remarques pour Madar:
# dans la doc, dire que le make_view prend au moins comme arguments
# workbench + l'outil

# c'est pas clair dans la doc que le processor va nous passer
#         workbench et engine

class AddTasksHook(BasePostExecutionHook):
    """Post-execusion hook to add a hierarchy of tasks.

    """
    root_task = Typed(RootTask) # dans Atom; à regarder
    default_path = Unicode()
    dependencies = Tuple()

    def __init__(self, declaration):
        """
        Create an empty root task
        """
        self.root_task = RootTask()
        super(BasePostExecutionHook, self).__init__(declaration=declaration)

    def check(self, workbench, **kwargs):
        """ Check that the post-hook task can be executed

        """
        # set the root_task default path to the one of the measure
        self.root_task.default_path = self.measurement.root_task.default_path
        res, traceback = self.root_task.check()
        return res, traceback

    def run(self, workbench, engine):
        """
        Execute the post-hook task
        l.390 dans processor
        remarque à Madar: c'est pas clair dans la doc que le processor va nous passer
        workbench et engine
        """
        meas = self.measurement
        meas_id = meas.id

        # get the build dependencies
        manager = workbench.get_plugin('exopy.tasks')
        # t_infos = manager.get_task_infos(self.root_task.task_id)
        # print('task infos', t_infos)
        # print('t_id', self.root_task.task_id, type(self.root_task.task_id))
        # t_id c'est juste une string exopy.ComplexTask
        # print('dependencies', t_infos.dependencies)
        # set of the dependancies id

        # vérifier que le list_runtimes est toujours appelé avt run
        deps = self.dependencies
        infos = ExecutionInfos(id=meas_id+'.posttask',
                                task=self.root_task,
                                build_deps=deps[0].dependencies,
                                runtime_deps=deps[1].dependencies,
                                observed_entries=[], # no monitor for the hooks
                                checks=not meas.forced_enqueued,
                                )
        execution_result = engine.perform(infos)
        print(execution_result)
        return execution_result

    def pause(self):
        """
        pause the task
        """
        self.engine.pause()

    def resume(self):
        """
        resume the task
        """
        self.engine.resume()

    def stop(self, force=False):
        """
        stop the task
        """
        self.engine.stop(force)

    def list_runtimes(self, workbench):
        """
        returns the run_time dependencies
        """
        cmd = 'exopy.app.dependencies.analyse'
        core = workbench.get_plugin('enaml.workbench.core')
        deps = core.invoke_command(cmd,
                                   {'obj': self.root_task,
                                    'dependencies': ['build', 'runtime']})
        self.dependencies = deps
        # print('collected deps', deps)
        return deps[1]

    # mesure collect_runtimes collects the pre/post hook dependencies
    # rq: on peut avoir un même tache dans monitor + post hook car elles ne vont pas être exécutées en même temps

    # parent de BasePostHook est BaseToolDeclaration (dans base_tool)
    # on voit que sur la mesure on a un get_state, set_state, mais pas sur le hook !
    # voir comment c'est appelé dans le workspace, et adapter éventuellement le workspace pour
    # pouvoir faire ça pour hooks


    # ajouter une option: à ne faire que si la mesure à échoué ?
    # cf doc: ‘task_execution_result’