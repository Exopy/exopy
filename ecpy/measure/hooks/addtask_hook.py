from .base_hooks import BasePostExecutionHook


class AddTasksHook(BasePostExecutionHook):
    """Post-execusion hook to add a hierarchy of tasks.
   
    """
    root_task = Typed(RootTask) # dans Atom; à regarder

    def check(self, workbench, **kwargs):
    '''
    check that the post-hook task can be executed
    appelé dans measure.py l.454
    '''
    # pour ajouter une tâche; où est-ce que je mets ça ? dans un init ?
    root_task.childen.append(task)
    test, traceback = root_task.check()


    def run(self, workbench, engine):
    '''
    execute the post-hook task
    l.390 dans processor
    remarque à Madar: c'est pas clair dans la doc que le processor va nous passer
    workbench et engine
    '''

    meas = self.measure
    meas_id = meas.id

    # infos = ExecutionInfos(id=meas_id+'.posttask',
    #                        task=self.root_task,
    #                        build_deps=deps.get_build_dependencies().dependencies,
    #                        runtime_deps=deps.get_runtime_dependencies('main'),
    #                        observed_entries=meas.collect_monitored_entries(),
    #                        checks=not meas.forced_enqueued,
    #                        )
    # regarder comment adapter ça... appelé l.308 dans engine

    # Ask the engine to perform the task
    execution_result = self.engine.perform(infos)


    def pause(self):
    '''
    pause the task
    '''
    self.engine.pause()


    def resume(self):
    '''
    resume the task
    '''
    self.engine.resume()


    def stop(self, force=False):
    '''
    stop the task
    '''
    self.engine.stop(force)


    def list_runtimes(self, workbench):
    '''
    returns the run_time dependencies
    '''
    # mesure collect_runtimes collects the pre/post hook dependencies
    # rq: on peut avoir un même tache dans monitor + post hook car elles ne vont pas être exécutées en même temps


    # note pour Lauriane
    # dans le processeur (pour start, stop) ou dans l'objet Measure (pour check),
    # il est prévu que ces méthodes soient appelées au bon moment.
    # c'est pour ça qu'il faut les définir ici dans le cas spécifique 
    # de notre hook (qui utilise notamment l'engine)

    # parent de BasePostHook est BaseToolDeclaration (dans base_tool)
    # on voit que sur la mesure on a un get_state, set_state, mais pas sur le hook !
    # voir comment c'est appelé dans le workspace, et adapter éventuellement le workspace pour
    # pouvoir faire ça pour hooks