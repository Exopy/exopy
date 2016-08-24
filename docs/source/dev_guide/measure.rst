.. _dev_measure:

.. include:: ../substitutions.sub

Measure and tools
=================

The measure system is at the heart of Ecpy. At the centre of a measure one
finds a hierarchy of tasks, but around it revolves a number of tools allowing
to customize its execution. This section will present the possibility of
extension Ecpy offers as far as the measure system is concerned.

.. note::

    Methods signature are not detailed and one should consult the docstrings of
    the base classes when implementing a new feature.

.. contents::

Tools
-----

Tools allow to customize what happens before and after the execution of the
task hierarchy when a task is run, they can also be used to report to the user
the progress of the measure.

.. note::

    As usual all declarations must possess a unique id and a description.

Pre_execution hooks
^^^^^^^^^^^^^^^^^^^

A pre-execution hook is run before the tasks attached to a measure. Actually a
pre-hook can have two purposes :

- extend the checks performed by the tasks. Some checks might requires to
  compare state of different tasks which is not possible from within the check
  method of task, on the contrary a pre-hook have access to the whole tree and
  is free to walk it.
- perform some custom actions before the task hierarchy is executed. It can for
  example run some initialisation procedure or query the state of some other
  part of the application before running the core of the measure.

Adding a pre-hook requires to :

- implement the logic by subclassing |BasePreHook|. The methods that can be
  overridden are :

  - check: make sure that the measure is in a proper state to be executed.
  - run: execute any custom logic. If any task is to be executed it should be
    executed by passing to the active engine.
  - pause/resume/stop: to implement is the run method execution can take a
    long time (typically if tasks are involved).
  - list_runtimes: let the measure know the runtime dependencies (such as
    instrument drivers) if any.

  Additionally if any entry is contributed to the task hierarchy they should
  be added when the tool is linked (or later during edition of the tool).

- declare it by contributing a |PreExecutionHook| to the
  'ecpy.measure.pre-execution' extension point. The declaration should
  re-declare the functions :

  - new: which should create a new instance of the tool.
  - make_view: which should create a widget used to edit the tool. If the tool
    has no user settable parameters this method can be ignored.

- If a make_view method has been declared then one needs to create the
  associated widget which should inherit of |Container|.


Monitors
^^^^^^^^

Monitors are used to follow the progress of a measure. They specify a number of
database entries they are interested in and will receive notifications when
the concerned entry is updated during the execution of the task hierarchy.

Adding a monitor requires to :

- implement the logic by subclassing |BaseMonitor|. The methods that can be
  overridden are:

  - start: Called when the execution of the task hierarchy is about to start.
    Prepare the monito to run.
  - stop: Called when the execution is over. Perform some clean up.
  - refresh_monitored_entries: Assume that the entries of the database are the
    one passed and determine which ones to monitor.
  - handle_database_entries_change: React to the addition/deletion/renaming of
    an entry from the database of the task hierarchy (happen only during
    edition time).
  - handle_database_nodes_change: React to the addition/deletion/renaming of
    a node in the database of the task hierarchy (happen only during
    edition time). Usually only renaming matters.
  - process_news: During execution, react to the update of an entry.

  Additionally the database entries to observe should be stored using their
  full path in the 'monitored_entries' member.

- declare it by contributing a |Monitor| to the 'ecpy.measure.monitors'
  extension point. The declaration should re-declare the functions :

  - new: which should create a new instance of the monitor.
  - create_item: which should create the widget displayed during the execution
    of the task hierarchy. This widget should inherit from |DockItem| and its
    name should be set when it is instantiated to the id of the monitor.

- To create the widget used to display the monitor informations. This widget
  should inherit from |DockItem|.


Post-execution hooks
^^^^^^^^^^^^^^^^^^^^

A post-execution hook is run after the tasks attached to a measure, and this no
matter the execution succeeded or not (save if the user stopped the measure and
asked not to run them). They are hence perfectly fitted to run clean up.

Adding a post-hook requires to :

- implement the logic by subclassing |BasePostHook|. The methods that can be
  overridden are :

  - check: make sure that the measure is in a proper state to be executed.
  - run: execute any custom logic. If any task is to be executed it should be
    executed by passing to the active engine. The post hook can inspect the
    measure it belongs to to identify whether the execution finished correctly
    ('task_execution_result' member).
  - pause/resume/stop: to implement is the run method execution can take a
    long time (typically if tasks are involved).
  - list_runtimes: let the measure know the runtime dependencies (such as
    instrument drivers) if any.

  Additionally if any entry is contributed to the task hierarchy they should
  be added when the tool is linked (or later during edition of the tool).

- declare it by contributing a |PostExecutionHook| to the
  'ecpy.measure.post-execution' extension point. The declaration should
  re-declare the functions :

  - new: which should create a new instance of the tool.
  - make_view: which should create a widget used to edit the tool. If the tool
    has no user settable parameters this method can be ignored.

- If a make_view method has been declared then one needs to create the
  associated widget which should inherit of |Container|.

.. note ::

    All tools shares the following methods that can be overridden as
    necessary (subclasses of |BaseMeasureTool|):

    - get_state: method used to save the state of the tool under the .ini
      format.
    - set_state: restore the state of a tool based of the parameters found
      in an .ini file
    - link_to_measure: method called when the tool is added to a measure.
    - unlink_from_measure: method called when the tool is removed from a
      measure.

Editors
-------

Editors are the GUI elements used to edit the different aspects of a task
hierarchy. Of course the most basic relies on the view associated to each task,
however to not crowd them it is interesting to move some settings to other
editors.

Adding an editor requires to :

- implement the GUI by subclassing |BaseEditor|. The methods that can be
  overridden are :

  - react_to_selection: which handles the editor being selected by the user.
  - react_to_unselection: which handles the editor being unselected by the
    user.

  Of course the editor should react to a change in its selected task.
  Additionally one can specify whether to hide/disabled the tree widget used
  to select the task when the editor is selected.

- declare it by contributing an |Editor| to the 'ecpy.measure.editors'
  extension point. The declaration should re-declare the functions :

  - new : which should create a new instance of the tool.
  - is_meant_for : which should determine if the editor fits the currently
    selected task. This method should be fast.


Engines
-------

Engines are responsible for the execution of task hierarchies (the main one of
course but also potentially those provided by the tools). A single engine can
be selected to be used by the system at a time.

Adding an engine requires to :

- implement the logic by subclassing |BaseEngine|. The methods that can be
  overridden are :

  - perform: which executes the given task.
  - pause/resume: which pauses/resumes execution. One can rely of the signals
    built-in the tasks.
  - stop: which stops the execution.
  - shutdown: which stops the engine.

- declare it by contributing an |Editor| to the 'ecpy.measure.editors'
  extension point. The declaration should re-declare the functions :

  - new: which should create a new instance of the tool.
  - react_to_selection: which should handle the fact that the engine has been
    selected to be used by the measure plugin.
  - react_to_unselection: which should handle the fact that the engine is no
    longer the one used by the measure plugin.
  - contribute_to_workspace: which can add GUI elements to the workspace.
  - clean_workspace: which should remove the any contributions from the
    workspace.
