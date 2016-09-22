.._measure_edition:

Measure edition
===============

So far this guide has only covered the basic edition of the tasks using the
tree view of the hierarchy and the standard editor. The following sections will
go further and explain how other editors can allow to fine tune the measure and
how to use the tools that are pre/post-execution hooks and the monitors.

.. contents::

.. measure_edition_editors:

Advanced use of editors
-----------------------

Dependending on the currently selected task, different editors can be
available :

- the standard editor used to edit the tasks is always present.
- the execution editor is also always present.
- the task database access editor is present for the tasks that can have
  children tasks.
- other editors contributed by plugins may be present for some tasks.

The standard editor provide a different view for each task depending on its
parameters and is hence the most commonly used.
For example, if you create a "Definition" task, it will appear in the standard
editor, first as a "Add first element" button, and then once you click on it
as two blank writing fields where you can enter a name and its definition.
A chevron button allows you to add another definition below.

The execution and database access editors present similar graphical user
interface for all tasks and are used to set common settings that would make
the standard editor unusable if they were present on it. They are available as
additional tabs above the tasks view. Their use is detailed in the next
sections.

Execution editor
^^^^^^^^^^^^^^^^

The execution editor as its name states can be used to edit the way a task will
be executed. Three parameters are editable :

- can the application be stopped/paused just before executing a task ? By
  default this is the case for all the tasks and has only a very limited
  overhead. This is controlled by the 'Stoppable' checkbox.
- should the task be executed in a new thread ? This setting controlled by the
  'Parallel' checkbox can be misleading in that in Python only one thread can
  execute python code at any time. However this constrained is released when
  calling C code (typically when performing IO operations such as writing into
  a file or communicating with an instrument). So if your experiment needs to
  set multiple instruments states before performing a measure you may gain
  time by doing the settings 'in parallel'. When executing a task in parallel
  it should be associated with a pool. A pool is nothing else than an id that
  will be used for synchronisation.
- should the task wait for any other task before running ? This is the pendant
  of the parallel setting: if a task is executed in parallel it may be crucial
  for another task to be sure that it has completed before running. This
  setting is controlled by the 'Wait' checkbox. When checked you can choose on
  which parallel pool to wait on (hence the id), or not to wait on some pools
  or to wait on all pools.

.. note::

    It is possible to run a task in parallel and have it wait on other pools.
    However note that the task will first wait in the main thread and then
    move the execution to another thread.

.. note::

    Running in task in parallel and waiting on pools can lead to small
    overheads in the task execution. Hence it is advised not to use those
    features in tight loops.

Database access exceptions
^^^^^^^^^^^^^^^^^^^^^^^^^^

The database access exception editor is available only on complex tasks (ie
tasks that have child tasks). It allows to change the visibility of the
values stored in the database. Let us explain this more precisely.

To each complex task is associated a node in the database, database which is
used by the tasks to store all sorts of data they may want to share. Each task
stores its values in the node of its parent. When a task needs to access a
value stored in the database by another task, it can only look into the values
stored in the same node it is storing its data or a higher node (the into which
its parent task is writing). However in some cases this can be restrictive,
lets give a more concrete example.

Consider a measure made of two parts:

- first a loop is run to acquire some data stored in an array.
- second the maximum of that array is extracted and use to an instrument before
  running a second loop.

The task filling the array is a child of the first loop. The task looking for
the max on the other hand is a child a the root it is hence not allowed to
access the array ! So this cannot work ! This is where the database access
editor enters the game.

In this editor panel, all the entries stored in the database are represented,
each one at the level of the node in which it is stored. To add an exception
simply right click the entry and choose 'Add access exception'. The entry will
be colored in lightblue and a new entry with a light green background will
appear in the parent node representing the exception. If you need to go further
up you can add an exception on the exception.

In the previous example we would simply have added an exception for the array
and we could have accessed it.


.. _measure_monitors_and_tools:

Monitors and tools
------------------

As briefly mentionned previously, pre/post execution hooks and monitors can be
added to a measure. To manage those 'tools', you must open the dedicated panel
by clicking on the 'Edit tools' button.

By default a single pre-hook is attached to the measure: the one responsible
for running the tests of the measure, it cannot be removed.

As usual you can add new tools using the add button and edit them when they are
selected. The use of pre/post hooks being pretty straightforward it will not be
detailed here.

Monitors can prove more tricky to use. First let us define what is the role of a
monitor (and hence what it is not supposed to do). A monitor is supposed to ask
for notifications when some entries are updated in the database and react to
that change in way that lets the user know what is currently going on. First
please note that this kind of notification can be time consuming and hence it is
better not to observe values inside tight loops (whose each iteration is around
30 ms). Second a monitor should strive for stability and low memory consumption
so that the measure does not crash because of it, which is why it should not
try to plot all the data acquired by the measure but leave this work to
external programs.

Ecpy comes with a built-in monitor which can display the values of the database
entries. It can perform some minimal formatting on those entries and you can
build new ones with custom formatting. It attached by default to all measures.

