.. _dev_tasks:

.. include:: ../substitutions.sub

Tasks and interfaces
====================

Tasks form the backbone of Ecpy measurement principle. A task represents an
action to perform during a measure. Tasks can be assembled in a hierarchical
manner with any level of nesting. Tasks support parallel execution (using
threads) and the associated synchronizations, they can also exchange data
through a common database.

This section will first focus on the minimal amount of work necessary to create
a new task and register it in Ecpy. This part will introduce another important
concept which is the one of interfaces whose creation will be detailed in the
following section. Finally more details about the internals of the tasks will
be discussed.

.. contents::

Creating a new task
-------------------

Creating a new task is a three step process :

- first the task itself which holds the logic must be created.
- to allow a user to correctly parametrize the task a dedicated widget or view
  should also be created.
- finally the task must be declared in the manifest of the plugin contributing
  it.

Implementing the logic
^^^^^^^^^^^^^^^^^^^^^^

The task itself should be a subclass either of |SimpleTask| or |ComplexTask|,
according to whether or not it can have children tasks attached to it. The
task parameters should be declared using the appropriate member and tagged with
'pref' in order to be correctly saved (the value does not matter). If a
parameter value can depend on values stored in the database, it should be
declared as a Unicode member to let the user enter a formula ('{' and '}' are
used to identify the part to replace with the value stored in the database).

.. code-block:: python

    from atom.api import Unicode, Int

    class MyTask(SimpleTask):
        """MyTask description.

        Use Numpy style docstrings.

        """
        #: my_int description
        my_int = Int(1).tag(pref=True)  # Integer with a default value of 1

        #: my_text description
        my_text = Unicode().tag(pref=True)

If the task needs to write a value in the database (typically all computed or
measured values should be stored), the entries should be declared by changing
the default value of the task_database_entries member. The provided value
should be a dictionary whose values specify the default value to write in the
database. Those values can also be altered during the edition of the task
parameters through its view by **assigning** a new dictionary to
task_database_entries.

.. code-block:: python

    from atom.api import set_default

    class MyTask(SimpleTask):
        """MyTask description.

        """
        task_database_entries = set_default({'val': 1})

The actual description of what the task is meant to do is contained in the
**perform** method which is the one you need to override (save when writing an
interfaceable task see next section). This method take either no argument, or a
single keyword argument if it can be used inside a loop in which case the
argument will be the current value of the loop. If subclassing |ComplexTask|
be sure to call the perform methods of all children tasks (stored in the
`children` member). Below is a list of some useful methods :

- |write_in_database|: is used to write a value in the database. In the
  database, values are stored according to the path to the task and its name,
  using this method you don't have to worry about those details you simply give
  the entry name and the value.
- |format_string|: this method format a string by replacing references to the
  database entries by their current value.
- |format_and_eval_string|: same as above but the resulting string is
  evaluated.

Depending on the complexity of the task you are creating you may also need to
write a custom **check** method. The check method is there to ensure that
everything is properly configured and that the task can run smoothly. It is
called every time the system need to check the state of the task. The checking
of formulas (either simply formatted or formatted and evaluated) is done
automatically in the base class check method. To take advantage of it, you
simply need to tag the concerned member with 'fmt' (formatting only) or 'feval'
(formatting and evaluation) (value should be True).

**You must always call the base class check method (using super).**

When to use interfaces
^^^^^^^^^^^^^^^^^^^^^^

It is quite common that due to some implementation details (such as using two
different instruments for example) you end up in a situation where you have two
almost identical tasks (up to some parameters) that basically do the same job
(or very similar ones). On top of being a naming nightmare such a situation
leads to code duplication which is something to be avoided (twice as many
tests, maintenance, etc).

To deal with such situations, Ecpy has a notion of interfaces for the tasks.
The idea is to delegate the actual execution to another object: 'the interface'
which is selected based on a parameters (the instrument to use, the method to
build an iterator, ...). Basically every task whose behavior is likely to be
extended should be an interfaceable task.

Creating an interfaceable task is easy, you simply need to mix your base class
with the |InterfaceableTaskMixin|, as follows:

.. code-block:: python

    class MyTask(InterfaceableTaskMixin, SimpleTask):

        pass

For such a class, you do not need to write a perform method however you may
want to write some generic methods that the interfaces can call (once again to
avoid code duplication). If your task has a well defined default behavior
fitting most cases (or if you are turning a non-interfaceable task into an
interfaceable one), you can define a kind of default interface by creating an
**i_perfom** method that will act as a default interface.

To learn more about interfaces in details please read the dedicated section
:ref:`dev_tasks_new_interface`.


Creating the view
^^^^^^^^^^^^^^^^^

All task views should inherit from |BaseTaskView| which is nothing more than
a customized GroupBox. From there you are free to design your UI the way you
want. To edit member corresponding to formulas with access to the database,
note that the |QtLineCompleter| and |QtTextCompleter| widgets give
auto-completion for the database entries after a '{'. You need to set the
entries_updater attribute to *task.list_accessible_database_entries*. If you do
so you may also want to use |EVALUATER_TOOLTIP| as a tool tip (tool_tip member)
so that your user get a nice explanation about he can and cannot write in this
field. From a general point of view it is a good idea to provide meaningful
tool tips.

.. code-block:: enaml

    enamldef MyTaskView(BaseTaskView):

        QtLineCompleter:
            text := task.my_formula
            entries_updater = task.list_accessible_database_entries
            tool_tip = EVALUATER_TOOLTIP

For more informations about the Enaml syntax please give a look at
:doc:`atom_enaml`.


At this point your task is ready to be registered in Ecpy, however writing a
bunch of unit tests for your test making sure it works as expected and will go
on doing so is good idea. Give a look at :doc:`testing` for more details about
writing tests and checking that your tests do cover all th possible cases.


Registering your task
^^^^^^^^^^^^^^^^^^^^^

The last thing you need to do is to declare your task in a plugin manifest so
that the main application can find it. To do so your plugin should contribute
an extension to 'ecpy.tasks.declarations' providing |Tasks| and/or |Task|
objects.

Let's say we need to declare a single task named 'MyTask'. The name of our
extension package (see :doc:`glossary`) is named 'my_ecpy_plugin'.
Let's look at the example below:

.. code-block:: enaml

    enamldef MyPluginManifest(PluginManifest):

        id = 'my_plugin_id'

        Extension:
            point = 'ecpy.tasks.declarations'

            Tasks:
                group = 'my_group'
                path = 'my_ecpy_plugin'

                Task:
                    task = 'my_task:MyTask'
                    view = 'views.my_task:MyView'
                    metadata = {'loopable': True}

We declare a single child for the extension a |Tasks| object. |Tasks| does
nothing by themselves they are simply container for grouping tasks
declarations. They have two attributes:

- group: this is simply to specify that the task is part of that group. Group
  are only used to filter tasks. (see :ref:`dev_tasks_new_filter`)
- path: when declaring a task you must specify in which module it is defined
  as a '.' sperated path. When declaring a path in a |Tasks| it will be
  prepended to any path-like declaration in all children.

We then declare our task using a |Task| object. A |Task| has four attributes
but only two of them must be given non-default values :

- task: this is the path ('.' separated) to the module defining the task. The
  actual name of the task is specified after a colon (':'). As mentioned above
  the path of all parent |Tasks| is preprended to this path.
- view: this identic to the task attribute but used for the view definition.
  Once again the path of all parent |Tasks| is preprended to this path.
- metadata: Any additional informations about the task. Those should be
  specified as a dictionary.
- instruments: This only apply to tasks using an instrument. In this attribute,
  the supported driver should be listed. Note that if a driver is supported
  through the use of an interface the driver should be listed in the interface
  and not in the task.

This is it. Now when starting Ecpy your new task should be listed.


.. _dev_tasks_new_interface:

Creating a new interface
------------------------


Minimal methods to implement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


When to use interfaces
^^^^^^^^^^^^^^^^^^^^^^


Creating the view
^^^^^^^^^^^^^^^^^


Registering your interface
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _dev_tasks_new_filter:

Creating your own task filter
-----------------------------

Creating your own task config
-----------------------------

