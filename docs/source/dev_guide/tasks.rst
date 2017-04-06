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
according to whether or not it can have children tasks attached to it.

The task parameters should be declared using the appropriate member and tagged
with 'pref' in order to be correctly saved. If the default way of
saving/restoring (repr/literal_eval) is enough simply use True as a value
otherwise you can specify the function to use to serialize/desarialize should
be passed as a tuple/list.

If a parameter value can depend on values stored in the database, it should be
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

Tasks use a common database (which is nothing else that a kind of smart
dictionary) to exchange data. If a task needs to write a value in the database
(typically all computed or measured values should be stored), the entries
should be declared by changing the default value of the |database_entries|
member. The provided value should be a dictionary whose values specify the
default value to write in the database. Those values can also be altered during
the edition of the task parameters through its view by **assigning** a new
dictionary to |database_entries|.

.. code-block:: python

    from atom.api import set_default

    class MyTask(SimpleTask):
        """MyTask description.

        """
        database_entries = set_default({'val': 1})

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
(formatting and evaluation) :

- for formatting only the value should be True, or 'Warn' if the error does not
  forbids to enqueue the measure.
- for formatting and evaluation it should be a |Feval| instance. See example.

.. code-block:: python

    import numbers
    from ecpy.tasks.api import validators as v

    class MyTask(SimpleTask):
        """MyTask description.

        """
        value1 = Unicode().tag(feval=v.Feval(types=numbers.Real,
                                             warn=True))

        value2 = Unicode().tag(feval=v.SkipEmpty())

        value3 = Unicode().tag(feval=v.SkipLoop())

In the above example :

- the value1 is always formatted and evaluated during the checks and the result
  should be a real number. If something goes amiss it won't be considered an
  outright error but the user will be warned.
- the value2 is checked only if a non-empty formula is passed.
- the value3 is checked only if the task is not embedded in a LoopTask.

Of course in case 2 and 3 types and warn could have been set. Note that types
can be a simple type or an iterable of types.

.. note::

    When validating on types be sure not to be too restrictive. For example
    if the output should behave like a float without any other restriction
    use numbers.Real that will also validate numpy.float32 where simply
    checking against float would fail.

.. note::

    The **check** method should not raise but add errors in the dictionary
    returned as second value. To avoid duplicate keys the path and name of the
    task  should be used. A preformatted key can be obtained by calling the
    **get_error_path** method.

If your task needs to run code once before the whole hierarchy execution
starts, you can over-write the **prepare** method which is called by the
|RootTask| before it starts to call its children perform method.


.. note::

    For task using instruments, the task should inherit from |InstrumentTask|
    that provides :

    - a 'selected_instrument' member storing all the data needed
      to start the instrument.
    - a 'check' method ensuring that those data makes sense.
    - a 'driver' member storing the driver instance after it has been created
      (the driver is created in prepare so the driver is always initialized in
      perform.)
    - a 'test_driver' method acting as a context manager that can be used to
      get a fully initialized driver to run additional checks.


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
so that your user get a nice explanation about what he can and cannot write in
this field. From a general point of view it is a good idea to provide
meaningful tool tips.

.. code-block:: enaml

    enamldef MyTaskView(BaseTaskView):

        QtLineCompleter:
            text := task.my_formula
            entries_updater = task.list_accessible_database_entries
            tool_tip = EVALUATER_TOOLTIP

All views have a reference to the view of the root task which provides some
useful methods to handle interfaces. It also holds a reference to the core
plugin of the application giving access to all the application commands
(see :doc:`application`). Views of tasks that can be embedded into a |LoopTask|
can declare an 'in_loop' boolean attribute, that will be set if they are used
for an embedded task.

For more informations about the Enaml syntax please give a look at
:doc:`atom_enaml`.

.. note::

    If your task accepts interfaces, the layout of your widget must be able to
    deal with it.

.. note::

    For tasks dealing with instruments, the view should derive from
    |InstrTaskView| which provides three widgets :

    - 'instr_label': a simple label describing the next widget.
    - 'instr_selection': a read only field displaying the currently selected
      profile and whose tool tip gives also the driver, connection and
      settings, with a button next to it to open the selection dialog.

    Those widgets should be integrated inside the view layout.


At this point your task is ready to be registered in Ecpy, however writing a
bunch of unit tests for your task making sure it works as expected and will go
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

- 'group': this is simply to specify that the task is part of that group. Group
  are only used to filter tasks. (see :ref:`dev_tasks_new_filter`)
- 'path': when declaring a task you must specify in which module it is defined
  as a '.' sperated path. When declaring a path in a |Tasks| it will be
  prepended to any path-like declaration in all children.

We then declare our task using a |Task| object. A |Task| has four attributes
but only two of them must be given non-default values :

- 'task': this is the path ('.' separated) to the module defining the task. The
  actual name of the task is specified after a colon (':'). As mentioned above
  the path of all parent |Tasks| is preprended to this path.
- 'view': this identic to the task attribute but used for the view definition.
  Once again the path of all parent |Tasks| is preprended to this path.
- 'metadata': Any additional informations about the task. Those should be
  specified as a dictionary. For example tasks which can be embedded in a loop
  should have an entry 'loopable' whose value is True.
- 'instruments': This only apply to tasks using an instrument. In this
  attribute, the supported driver should be listed. Note that if a driver is
  supported through the use of an interface the driver should be listed in the
  interface and not in the task. Driver should be listed by specifying their id
  ie top_package.architecture.class_name. If this field is specified, the task
  should be a subclass of |InstrumentTask| or have a selected_instrument member
  similar to the one of |InstrumentTask|.
- 'dependencies' : If the task has rutime dependencies other than instruments
  the ids of the corresponding analysers should be listed here.

This is it. Now when starting Ecpy your new task should be listed.

.. note::

    You can also alter the metadata/instruments of a task by redeclaring it and
    only specify the **id** of the task (not the full path) and omit the view.
    This can be used for example to declare that the task support a new
    instrument (added by your extension). The id of the task is formed by the
    top level package declaring it followed by the name of the task. This
    allows to declare tasks with the same name in different extension packages.

    ex : ecpy.LoopTask


.. _dev_tasks_new_interface:

Creating a new interface
------------------------

Creating a new interface is very similar to creating a new task and the same
three steps exists :

- first the interface itself which holds the logic must be created.
- to allow a user to correctly parametrize the interface one or several widgets
  should also be created, how those widgets will be laid out is the
  responsibility of the task view.
- finally the interface must be declared in the manifest of the plugin
  contributing it.


Minimal methods to implement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The interface should be a subclass either of |TaskInterface| or |IInterface|,
according to whether it is an interface for a task or an interface for an
interface (more on that later). Apart from that, the declaration of an
interface is similar to the one of a task. The same method needs to be
implemented and the handling of the database use the same members.

.. code-block:: python

    from atom.api import Unicode, Int

    class MyInterface(TaskInterface):
        """MyInterface description.

        Use Numpy style docstrings.

        """
        #: my_int description
        my_int = Int(1).tag(pref=True)  # Integer with a default value of 1

        #: my_text description
        my_text = Unicode().tag(pref=True)

        database_entries = set_default({'val': 1})

.. note::

    The useful methods cited on in task section are available only on the task
    not on the interface, so you need to access to them through the task (via
    the *task* member)

.. note::

    The check method of the interface is called before the check method of the
    task hence the interface should not crash if some values expected from the
    task are not available. It does not need to report those issues as the
    task is supposed to do so.


When to use interfaces
^^^^^^^^^^^^^^^^^^^^^^

The problem solved for tasks by using interfaces can be found also interfaces.
That's why Ecpy allow to have interfaces for interfaces without depth limit.
Declaring an interfaceable interface is done in the same way, an interfaceable
task. The only difference is the use of the |InterfaceableInterfaceMixin| class
instead of the |InterfaceableTaskMixin|.


Creating the view(s)
^^^^^^^^^^^^^^^^^^^^

Just like for task, you need to provide a widget to edit the interface
parameters. Actually for interfaces you can provide several. Whether you need
one or several depends on the task your interface plugs into.

Because of this freedom, there is no base widget for interfaces. However to
work correctly, your views should always declare a *root* attribute (to which a
reference to the view of the root task is assigned) and an *interface*
attribute (in which a reference to the interface is stored).

.. code-block:: enaml

    enamldef MyInterfaceView(Container):

        #: Reference to the RootTask view.
        attr root

        #: Reference to the interface to which this view is bound.
        attr interface


Registering your interface
^^^^^^^^^^^^^^^^^^^^^^^^^^

Registering an interface is quite similar to registering a task with the
notable difference that the interface need to know to which task or interface
it is bound.

Let's say we need to declare an interface named *MyInterface*. This interface
is linked to *MyTask*. The name of our extension package (see :doc:`glossary`)
is 'my_ecpy_plugin'.
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

                    Interfaces:
                        path = 'interfaces'

                        Interface:
                            interface = 'my_interface:MyInterface'
                            views = ['views.my_interface:MyInterfaceView']

Here we simply added an |Interface| as a child of the declaration of *MyTask*
presented in the previous section. Because it is a child of the *MyTask*
declaration it will automatically infer that the parent task is *MyTask*.
Furthermore, both the |Tasks| path and the |Interfaces| path will be prepended
to the interface and views attributes.

.. note ::

    The group attribute of |Interfaces| even when specified is unused.

However when declaring an interface for an existing task, redeclaring the task
would be tedious that's why the |Interface| has an *extended* member. This
member expect a list with the id of the task to which this interface
contributes. If the interface contribute to an interface the task and all the
intermediate interfaces should be listed (the task being the first in the
list). Contributing to the |LoopTask| for example would look like that for
example :

.. code-block:: enaml

    enamldef MyPluginManifest(PluginManifest):

        id = 'my_plugin_id'

        Extension:
            point = 'ecpy.tasks.declarations'

            Interfaces:
                path = 'my_ecpy_plugin.interfaces'

                Interface:
                    interface = 'my_interface:MyInterface'
                    views = ['views.my_interface:MyInterfaceView']
                    extended = ['ecpy.LoopTask']

.. note::

    |Interface|, like |Task| has a *metadata* and an *instruments* members
    which have the exact same functionalities.  If *instruments* is specified,
    the interface should have a selected_instrument member similar to the one
    of |InstrumentTask| or be linked to an interface/task that does.


.. _dev_tasks_new_filter:

Creating your own task filter
-----------------------------

As the number of tasks available in Ecpy grows, finding the task you need might
become a bit tedious. To make searching through tasks easier Ecpy can filter
the tasks from which to choose from. A number a basic filters are built-in but
one can easily add more.

To add a new filter you simply need to contribute a |TaskFilter| to the
'ecpy.tasks.filters' extension point, as in the following example :

.. code-block:: enaml

    enamldef MyPluginManifest(PluginManifest):

        id = 'my_plugin_id'

        Extension:
            point = 'ecpy.tasks.filters'

            TaskFilter:
                id = 'MyTaskFilter'
                filter_tasks => (tasks, templates):
                    return sorted(tasks)[::2]

A filter need a unique *id* (basically its name) and a method to filter through
tasks. This method receives two dictionaries: the first ones contains the known
tasks and their associated infos, the second the templates names and their
path. Here we overrode the *filter_tasks* method (see :doc:`atom_enaml` for
more details about the syntax), we could also have used one of the following
specialized filters:

- |SubclassTaskFilter|: filter the tasks (exclude the templates) looking for
  a common subclass (declared in the *subclass* attribute)
- |MetadataTaskFilter|: filter the tasks (exclude the templates) based on the
  value of a metadata (*meta_key* is the metadata entry to look for,
  *meta_value* the value looked for).
- |GroupTaskFilter|: filter the tasks (exclude the templates) belonging to a
  common group (*group* member).


Creating your own task configurer
---------------------------------

In some cases, the default way to configure a task before inserting it in a
task hierarchy (ie simply specifying its name) is not enough. It is for example
the case of the |LoopTask| for which we also need to configure its subtask if
there is one. The task configurers exist to make possible to customize the
creation of a new task. Creating one is once again similar to creating a new
task.

.. note::

    Task configurers are not meant to fully parametrize a task, the task view
    is already there for that purpose. It is rather meant to provide essential
    informations necessary before including the task in a hierarchy or
    parameters not meant to change afterwards.

.. note::

    When a task configurer is specified for a task it is by default used form
    all its subclasses too.

Minimal methods to implement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All task configurers need to inherit from |PyTaskConfig|, which defines the
expected interface of all configurers. When creating a new configurer two
methods need to be overwritten :

- build_task : this method is supposed to return when called a new instance of
  the task being configured correctly initialized. The configurer holds a
  refrence to the class of the task it is configuring.

- check_parameters : this method should set the *ready* flag to *True* if all
  the parameters required by the configurer have been provided and *False*
  otherwise. It should be called each time the value of a parameter change
  (using a *_post_settattr_\** method).

.. code-block:: python

    class MyTaskConfig(PyTaskConfig):
        """Config for MyTask.

        """
        #: My parameter description
        parameter = Int()

        def check_parameters(self):
            """Ensure that parameter is positive and task has a name.

            """
            self.ready = self.parameter and self.task_name

        def build_task(self):
            """Build an instance of MyTask.

            """
            return self.task_class(name=self.task_name,
                                   parameter=self.parameter)

        def _post_setattr_parameter(self, old, new):
            """Check parameters each time parameter is updated.

            """
            self.check_parameters()

Creating the view
^^^^^^^^^^^^^^^^^

Just like for tasks and interfaces, you need to create a custom widget to
allow the user to parametrize the configurer. Your widget should inherit from
|PyConfigView|. This widget is simple container with a label and a field to
edit the task name. Furthermore it has two attributes :

- config : a reference the task configurer being edited.
- loop : a bool indicating whether or not the task is meant to be embedded in
  a loop.

Declaring the configurer
^^^^^^^^^^^^^^^^^^^^^^^^

Finally you must declare the config in a manifest by contributing an
extension to the 'ecpy.tasks.configs' extension point. This is identical to
how tasks are declared but relies on the |TaskConfigs| (instead of |Tasks|) and
|TaskConfig| (instead of |Task|) objects. The base task class for which the
configurer is meant should be returned by the get_task_class method.


More on tasks internals
-----------------------

Parallel execution, waiting, stopping and pausing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For any task one can specify a number of parameters concerning how the
|perform| is called :

- should the task be executed in another thread (ie in parallel) of the rest of
  the execution. This is controlled by the value of the |parallel| attribute.
  Threads are grouped by pool to simplify the synchronization issues.
- should the task wait on any other task before running. This is controlled by
  the |wait| attribute. One can specify whether to wait for all threads to
  proceed or only on some pools (or to wait for all threads save the ones in
  some pools).
- should one be able to stop the execution of the whole hierarchy or set it on
  pause when calling this task.

To give that flexibility, the actual *perform* method of the task is wrapped
when running the *check* method and it is partly why it is vital to always call
the |BaseTask| *check* method.

.. note::

    First the condition for stopping/pausing is checked, then the task wait for
    other to terminate and finally the task is executed in parallel if
    parametrized to do so.

.. note::

    Please note that if waiting from a thread one must be careful not to wait
    on the pool from which it is part. For example, if a ComplexTask is
    performed in parallel all child task must be careful not to wait upon the
    pool to which the ComplexTask belong.


Database access and exceptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As stated above, tasks use a common database to exchange data. This database is
organized hierarchically like the tasks themselves. To each |ComplexTask|, will
be associated a node in the database. Each task can write in the database in
the node of their parent (ie a |ComplexTask| does not write into its own node,
only the |RootTask| does this).

By default a task can only access to the entries written in the same node, it
can write or in nodes higher in the hierarchy. However, it is sometimes
desirable to relax this constraint. One such case is when a |ComplexTask| is
used to isolate a complex operation, but following tasks need to access results
of some inner tasks of the previously cited |ComplexTask|. To do so, the
database has a notion of *access exceptions*, which basically make an entry
appears on the node its original node (and exceptions can be chained to go up
as many times as necessary).

From the developer point of view, this does not change anything, as he does not
need to do anything in the task to allow this.

Shared resources
^^^^^^^^^^^^^^^^

The database is the right way to exchange data such as numbers and arrays
between tasks. However some tasks can also access to other kind of resources
such as instruments or file descriptors. Generally such resources need to be
properly initialized and more importantly finalized. Furthermore they can be
shared by multiple tasks, suggesting a thread-safe way to store and manipulate
them. As a task is not aware of whether or not it will be called again in the
future, it cannot properly close its resource (as closing and re-opening a
resource repeatedly is most likely time costly). That's why such resources
should be stored in special containers in the |resources| attributes of the
|RootTask|. The |resources| attributes is a dictionary, the keys allowing
to easily retrieve the wanted container.

For each kind of object to store, one should create a subclass of
|ResourceHolder| implementing the *release* and *reset* methods (look at the
API docs for more details). When first creating a resource, check whether
or not the right container already exists in the |resources| attribute or not,
and store the newly created resource.

At the end of the *perform* method of the |RootTask|, all the stored resources
are properly released avoiding any corruption.


Edition mode vs running mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some places in the code, one may find references to the notion of running
mode for the database. This mode should be activated when the edition of the
tasks hierarchy is over as it allows to speed up a number of operations. In
running mode, the databased is flattened to allow fast repeated access to the
same entry by first querying its index and then using that index for getting
the value. Because of this, no entry can be added or removed from the database.
Another optimization is performed by caching a pre-evaluated version of all
formulas used in tasks.
