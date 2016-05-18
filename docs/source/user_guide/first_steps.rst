.. _first_steps:

First steps
===========

Once you have installed Ecpy you are ready to set it up, then prepare and run 
your first measure. The following sections will take you through those steps.
More details about the instruments and how to customize your measure will be 
given later on in this manual.

.. contents::

Starting the application
------------------------

You can start Ecpy either using the Anaconda Launcher, or simply using the 
ecpy command at the command line::

    $ ecpy
    
If you are starting Ecpy for the first time, you will be prompted to choose a 
folder in which the application will store a number of settings and also write
the log file. In the following of this guide this directory will be referred to
as the **application directory**.

When the application starts you should see this window::

.. todo:: add main window image

.. note::

    The first start up can be pretty slow as the application need to compile 
    the  application graphical user interface, but as the result of this 
    process is cached subsequents start ups should be much faster. 

The different panels can be re-organized, tabbed or reduced. The bottom panel
is used for log messages, it will display messages from the application.
The left top panel is used to edit measures, actually multiple measures can be
edited at the same time and similar panels will be opened if necessary. The 
right top panel display the measures waiting to be performed.

The next sections will detail how those panels work.

.. note::

    The command line command accepts some optional arguments, use::
        
        $ ecpy -h 
        
    To learn more about the supported options.

.. note::

    If you installed a broken extension package, Ecpy may fail to start. If 
    that is the case, the application should display a dialog explaining the
    issue. The easiest way to fixit is to uninstall the offending package
    and report the bug to its maintainer. If nothing works, and you have 
    already set the application directory, you can give alook at the log file.
    If nothing works do not hesitate to contact the maintainer.
    
.. note::

    Ecpy is made out of different plugins providing different capabilities.
    To make the application start up faster, only the needed plugin are 
    actually started when the application starts. When a new plugin starts, if
    any error happens a dialog will show up describing the errors that 
    occurred. At any time you can access a summary of those issues under the 
    menu **Tools/Show errors report**.
    
Creating a measure
------------------

A measure is made of different pieces :

- a hierarchy of tasks to perform.
- a set of tools which are most of them optional.

The tasks are the true backbone of the measure. Each one describe an elementary
step of the measure. They are organized in a tree structure hence allowing more
flexibility than simply nested loops. Tasks can be pass information between 
through a shared database.

The tools are optional and allow to customize three parts of the execution:

- pre-execution hooks are run before starting the actual measurement and can
  be used to validate the parameters in the measure or collect the state of the
  application.
- monitors are active while the main part of the measure is running and can 
  report on the progress of the measure.
- post-execution hooks are run after the main part of the measure has been 
  executed and can run even if the main part of measure errored.
  
When creating a new blank measure (using the **File/New measure** menu), the 
panel added to the graphical interface allows you to edit the tasks, to edit
the tools you need to click the **Edit tools** button. The edition of tools 
will be described in ???.

Each measure have a name, an id and a root directory. The name is intented to 
describe the purpose of the measure while its id can act as a counter to 
discriminate multiple execution of the same measure. The root directory is used
to save the measure and the log file associated with the measure and can also 
be accessed by the tasks to serve as root directory to save the measure data.

The task hierarchy starts empty with only a root task. From there you can use
either the tree or the buttons in the right panel to add more tasks. The tree 
view can also be used to re-organize the tasks and rename them. The panel on 
the right contains the editors organized in tabs. By default the standard 
editor is selected and allow to parametrize the tasks. For basic measure, this
editor is sufficient (the role of the other will be described in ???).

Once you click to add a task, a dialog allow you to select the task to add.
When selecting a task a description will appear on the right and if the task
necessitates some parametrization the appropriate tools will be provided. Each
task need a name, by default a name is provided but for clarity sake it may
be best to change it.

Once the task is added to the hierarchy, you can edit its parameters. A number 
of them can be specified as formulas following the python syntax (in this case
the tooltip of the widget should give a hint about what is expected and allowed
in the field). In the formula fields, one can access the values stored in the
database using the following syntax : {TaskName_entryname}. The fields provide
autocompletion suggesting the different possibilities and hence avoid the 
need to remember all the possibilities.

.. note::

    In the standard editor the small button shown close to each task can be use 
    to add/move/remove the tasks.
    
.. note::

    For task using a physical instrument, you need to specify the instrument to
    use. How to register an instrument so that it can be selected in the task
    is explained in the next section.
    
Once you are happy with your measure you can save it using either the menu or
the button in the panel. Measures are saved in under the '.ini' format which
is text based and can easily be re-edited if need be.

.. note::

    You can also save a measure using 'Ctrl+S'. If you are editing multiple 
    measures, the last measure you selected will get saved.
    
The last step before executing your measure is to enqueue it. When enqueueing
a measure automatic checks are run validating for instance that all the 
formulas entered can be evaluated. If the checks pass the measure will appear
as enqueued, **BUT** the editor won't be closed it must nonetheless be noted 
that editing this measure **won't change** the state of the enqueued measure.
If some checks do not pass or raise some warning a dialog will pop-up. If only
warnings where emitted (for example the measure will override some existing
files), you can choose to enqueue the measure nonetheless. Actually even if 
some errors occurred you can force the enqueueing but you should have a very 
good reason to do so.

.. note::

    You can re-edit an enqueued measure by opening a dedicated dialog using the
    button nect to the measure name in the queue.

Congratulations your measure is now waiting for execution. The next setion will
describe how to start it and what happens next.

Running a measure
-----------------

Starting the measure is straightforward as you simply have to click on the 
'Start' button. If no 'engine' is currently selected (an engine is responsible 
for executing the tasks), you will be prompted to choose one. The default one
coming with Ecpy will add another log panel just by the one use by the 
application.

For each enqueued measure, the execution will happen as follow:

- the checks are run once again as at enqueuing time some of them may have been
  skipped (for example if measure was using an instrument, its properties
  could not be tested).
- the pre-execution hooks are executed
- the main task is handed over to the engine for execution. It is at this step
  that the monitors will be started if you attached any to your measure.
- the post-execution hooks are called.

.. note::

    If a hook also execute tasks, it will also hand them over to the engine
    for execution.
    
At any step of the execution, you can pause the measure or stop. Note however,
that if a long running task is under way and it does listen for the proper 
signals you may have to wait for this task to complete before seing the 
execution pause or stop. 

Pausing can be handy if you need to manually change a parameter on one 
instrument for example. When you will resume the measure, all previously known
states of the instruments will be re-initialized so that your intervention does
not affect the state of the measure.

When stopping a measure, you will be asked whether you want or not to run the 
post-execution hooks (if any is present). This is so because you may have 
included safety settings in the post hook and you hence need to be sure they 
will be executed. Note that when stopping, you either stop the current measure
but execute the next ones or stop everything.

.. note::
    
    After trying to properly stop a measure, you will be offered to force the
    operation. This should have an immediate effect on the measure execution
    but may leave some systems (the VISA library) in an undefined state.
    
.. note::

    While a measure is running the application will prevent closing to avoid
    crashing everything by clicking accidentally on the 'x' button.
    
Those are the basics, but to be able to run a meaningful measure you will need
to use some instruments. The next section will explain how those are handled in
Ecpy and how to register one so that it can be used in a measure.
    