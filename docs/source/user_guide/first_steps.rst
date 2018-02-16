.. _first_steps:

First steps
===========

Once you have installed Exopy you are ready to set it up, then prepare and run
your first measurement. The following sections will take you through those steps.
More details about the instruments and how to customize your measurement will be
given later on in this manual.

.. contents::

Starting the application
------------------------

You can start Exopy either using the Anaconda Launcher, or simply using the
exopy command at the command line::

    $ exopy

If you are starting Exopy for the first time, you will be prompted to choose a
folder in which the application will store a number of settings and also write
the log file. In the following of this guide this directory will be referred to
as the **application directory**.

When the application starts you should see this window::

.. todo:: add main window image

.. note::

    The first start up can be pretty slow as the application needs to compile
    the  application graphical user interface, but as the result of this
    process is cached subsequent start ups should be much faster.

The different panels can be re-organized, tabbed or reduced. The bottom panel
is used for log messages, it will display messages from the application.
The top left panel is used to edit measurements, actually multiple measurements can be
edited at the same time and similar panels will be opened if necessary. The
top right panel display the measurements waiting to be performed.

The next sections will detail how these panels work.

.. note::

    The exopy command accepts some optional arguments. Use::

        $ exopy -h

    To learn more about the supported options.

.. note::

    If you installed a broken extension package, Exopy may fail to start. In
    that case, the application should display a dialog explaining the
    issue. The easiest way to fix it is to uninstall the offending package
    and report the bug to its maintainer. If nothing works (and you have
    already set the application directory), you can have a look at the log file.
    If nothing works do not hesitate to contact the maintainer.

.. note::

    Exopy is made out of different plugins providing different capabilities.
    To speed up the application start-up, only the needed plugin are
    actually started when launching it. When a new plugin starts, a dialog will
    show up describing the error(s) if any occurred. At any time you can access
    a summary of those issues under the menu **Tools/Show errors report**.

Creating a measurement
------------------

A measurement is made of different pieces :

- a hierarchy of tasks to perform.
- a set of tools which are mostly optional.

The tasks are the true backbone of the measurement. Each one describes an elementary
step of the measurement. They are organized in a tree structure hence allowing more
flexibility than simply nested loops. Information can be passed between Tasks
through a shared database.

When creating a new blank measurement (using the **File/New measurement** menu), the 
panel added to the graphical interface allows you to edit the tasks and the 
tools. This panel contains a tree view of the task hierarchy and to its right 
the different editors, organized in tabs, that can be used to edit the 
hierarchy. To edit the tools, you need to click the **Edit tools** button ; the 
edition of tools will be described in :ref:`measurement_monitors_and_tools`

Each measurement has a name, an id and a root directory. The name is intented to
describe the purpose of the measurement while its id can act as a counter to
discriminate multiple execution of the same measurement - it should be a unique
identifier. The root directory is use to save an '.meas.ini' file corresponding 
to the measurement and the associated log file. It can also be accessed by the tasks
to serve as root directory to save the measured data.

The task hierarchy starts empty, with only the root task. From there you can use
either the tree context menu or the button in the editor to the right of the 
tree to add a first task. Further tasks can be added using the context menu of 
the tree or the '>' in the standard editor (selected by default). The tree view
can also be used to rename the tasks and re-organize them with drag-and-drops.
The standard editor allows to set most of the tasks parametersand is sufficient
for basic measurement (the role of the other will be described in 
:ref:`measurement_edition_editors`).

Once you click to add a task, a dialog window opens to allow you to select a task.
When selecting a task, a description will appear on the right and if the task
necessitates some parametrization the appropriate tools will be provided. Each
task needs a name ; one is provided by default but for clarity sake it may
be best to change it.

.. warning::

    It is not possible to have two Tasks with the same name at a given nesting
    in the hierarchy.

Once the task is added to the hierarchy, you can edit its parameters. A number
of them can be specified as formulas following the python syntax (in this case
the tooltip of the widget should give a hint about what is expected and allowed
in the field). In the formula fields, one can access the values stored in the
database using the following syntax : {TaskName_entryname}. The fields provide
autocompletion, suggesting the different possibilities and hence avoiding the
need to remember all the possibilities.

.. note::

    In the standard editor the small button shown close to each task can be use
    to add/move/remove the tasks.

.. note::

    For task using a physical instrument, you need to specify the instrument to
    use. How to register an instrument so that it can be selected in the task
    is explained in the next section.

Once you are happy with your measurement you can save it using either the menu or
the button in the panel. Measures are saved under the '.ini' format which
is text-based and can easily be re-edited if need be.

.. note::

    You can also save a measurement using 'Ctrl+S'. If you are editing multiple
    measurements, the last measurement you selected will be saved.

The last step before executing your measurement is to enqueue it. When enqueueing
a measurement automatic checks are run, validating for instance that all the
formulas entered can be evaluated. If the checks pass the measurement will appear
as enqueued, **BUT** the editor won't be closed. It must nonetheless be noted
that editing this measurement **won't change** the state of the enqueued measurement.
If some checks do not pass or raise some warning a dialog will pop-up. If only
warnings where emitted (for example the measurement will override some existing
files), you can choose to enqueue the measurement nevertheless. Actually even if
some errors occurred you can force the enqueueing but you should have a very
good reason to do so.

.. note::

    You can re-edit an enqueued measurement by opening a dedicated dialog using the
    button next to the measurement name in the queue.

The next section will shortly review aditional options to customize the measurement,
before moving on to the execution.


Editing the tools
^^^^^^^^^^^^^^^^^

The tools are optional and allow to customize three parts of the execution:

- pre-execution hooks are run before starting the actual measurement and can
  be used to validate the parameters in the measurement or collect the state of the
  application.
- monitors are active while the main part of the measurement is running and can
  report on the progress of the measurement.
- post-execution hooks are run after the main part of the measurement has been
  executed and can run even if the main part of measurement failed.

More details can be found in :ref:`measurement_monitors_and_tools`.

Congratulations, your measurement is now waiting for execution ! The next section
will describe how to start it and what happens next.

Running a measurement
-----------------

Starting the measurement is straightforward as you simply have to click on the
'Start' button. If no 'engine' is currently selected (an engine is responsible
for executing the tasks), you will be prompted to choose one. The default one
coming with Exopy will add another log panel just by the one use by the
application.

For each enqueued measurement, the execution will happen as follow:

- the checks are run once again as at enqueuing some of them may have been
  skipped (for example if a running measurement was using an instrument, its 
  properties could not be tested).
- the pre-execution hooks are executed.
- the main task is handed over to the engine for execution. It is at this step
  that the monitors will be started if you attached any to your measurement.
- the post-execution hooks are called.


.. note::

	The engine is responsible for the execution of tasks. Exopy comes with a 
	builtin one executing the tasks in a different process to limit 
	interferences between the edition and the execution of measurement.

.. note::

    If a hook also executes tasks, it will also hand them over to the engine
    for execution.

At any step of the execution, you can pause the measurement or stop. Note however,
that if a long running task is under way and it does listen for the proper
signals you may have to wait for this task to complete before seeing the
execution pause or stop.

Pausing can be handy if you need to manually change a parameter on one
instrument for example. When you resume the measurement, all previously known
states of the instruments will be re-initialized so that your intervention does
not affect the state of the measurement.

When stopping a measurement, you will be asked whether you want or not to run the
post-execution hook(s) (if any is present). This is because you may have
included safety settings in the post hook, hence you need to be sure they
will be executed. Note that when stopping, you choose to either stop the
current measurement and execute the next ones or stop everything.

.. note::

    After trying to properly stop a measurement, you will be offered to force the
    operation. This should have an immediate effect on the measurement execution
    but may leave some systems (the VISA library) in an undefined state.

.. note::

    While a measurement is running the application will prevent closing to avoid
    crashing everything by clicking accidentally on the 'x' button.


Those are the basics, but to be able to run a meaningful measurement you will need
to use some instruments. The next section will explain how those are handled in
Exopy and how to register one so that it can be used in a measurement.
