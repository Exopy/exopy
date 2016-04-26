.. _dev_application:

.. include:: ../substitutions.sub

Interacting with the core of Ecpy
=================================

This section will focus on the functionality offered by the plugins
constituting the core of the Ecpy application and how custom plugin can use
and or extend those functionalities.

.. contents::

Providing application wide commands and sharing state
-----------------------------------------------------

One usual need in plugin application is to make available to all other part of
the application some function (for example the possibility to request the use
of a driver) or to let other part of the application what is the state of a
plugin (for example a list of all the available drivers).

One could of course directly access the plugin to get those informations but
in a plugin application it is a good to avoid such interferences. Those
informations are actually delegated to two plugin responsible for managing
them :

- the 'enaml.workbench.core' plugin is in charge of managing commands which are
  the equivalent of application wide available function. Each command has an
  id which is used to invoke it using the |invoke_command| of the |CorePlugin|
  (this is the only case in which one needs to access directly to a plugin).
  When invoking a command one must pass a dictionary of parameters and can
  optionally pass the invoking plugin. To know what arguments the command
  expect you should look at its description in the manifest of the plugin
  contributing it.
- the 'ecpy.app.states' plugin is in charge of managing states which allow to
  get access to a read-only representation of some of the attributes of a
  plugin. The state of a plugin can be requested using the Command
  'ecpy.app.states.get' with an id parameters identifying the plugin
  constituting the state. If you need to access to such a state you should
  observe the alive attribute which becomes `False` when the plugin
  contributing the state is unregistered.

Declaring a Command
^^^^^^^^^^^^^^^^^^^

In order to declare a command, you must contribute an |Command| object to the
'enaml.workbench.core.commands'  extension point. A |Command| must have :

- an id which must be unique (this a dot separated name)
- a handler which is a function taking a argument an |ExecutionEvent| instance.
  The execution event allows to access to the application workbench
  ('workbench' attribute) and to the parameters ('parameters' attribute) passed
  to the |invoke_command| method. IF the command need to access
  to the plugin you can do so easily using the workbench.
- a description which is basically the docstring of the command and should be
  formatted as such (see :doc:`style_guide`).

Declaring a State
^^^^^^^^^^^^^^^^^

In order to share the state of your plugin you must contribute a State object
to the 'ecpy.app.states.state' extension point. A |State| must have :

- an id which must be unique and can be the id of the plugin but does not have
  to.
- the names of the members of the plugin the state should reflect (as a list).
- an optional description.


Customizing application start up and closing
--------------------------------------------

In some cases, a plugin needs to perform some operation at application start up
(for example discover extension packages, or adding new logger handlers) or
some special clean up operations when the application exits. It may also need
to have a say so about whether or not the application can exit (if a measure
is running the application should not exit without a huge warning). The
'ecpy.app' plugin is responsible for handling all those possibilities. It
relies on three extension points (one for each behaviour) :

- 'ecpy.app.startup' accepts |AppStartup| contributions and deal with the start
  up of the application.
- 'ecpy.app.closing' accepts |AppClosing| contributions and deal with whether
  or not the application can be closed.
- 'ecpy.app.closed' accepts |AppClosed| contributions to run clean up operation
  before starting to unregister plugins.

.. note::

   The customisation of the start up and exit of the application should only be
   used for operations not fitting into the |Plugin.start| and |Plugin.stop|
   methods of the plugin. This customization fits operations that must be
   performed at application start up and cannot be deferred to plugin starting,
   or clean up operations requiring the full application to be active (ie not
   dependent only on the plugin state).

Declaring an AppStartup extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to customize the application start up, you need to contribute an
|AppStartup| object to the 'ecpy.app.startup' extension point. An |AppStartup|
must have :

- an id which must be unique and can be the id of the plugin but does not have
  to.
- a run attribute which must be a callable taking as single argument the
  workbench.
- a priority, which is an integer specifying when to call this start up.

.. note::

    Start up are called from **lowest** priority value to highest and by their
    order of discovery if they have the same priority. The default priority is
    20.


Declaring an AppClosing extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to customize how the application determine whether or not it can exit,
you need to contribute an |AppClosing| object to the 'ecpy.app.closing'
extension point. An |AppClosing| must have :

- an id which must be unique and can be the id of the plugin but does not have
  to.
- a validate attribute which must be a callable taking as arguments the
  main window instance (from which the workbench can be accessed) and the
  |EventClose| associated with the attempt to close the application. If the
  plugin determine that the application should not be closed, it should call
  the |EventClose.reject| method of the |EventClose|.


Declaring an AppClosed extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to customize the application closing, you need to contribute an
|AppClosed| object to the 'ecpy.app.closed' extension point. An |AppClosed|
must have :

- an 'id' which must be unique and can be the id of the plugin but does not
  have to.
- a 'clean' attribute which must be a callable taking as single argument the
  workbench.
- a priority, which is an integer specifying when to call this start up.

.. note::

    Closed are called from **lowest** priority value to highest and by their
    order of discovery if they have the same priority. The default priority is
    20.


Using the built in preferences manager
--------------------------------------

If any of your plugin need to retain user preferences from one application run
to the next it should use the built-in preferences management system, which
is straightforward. First your plugin should inherit from
|HasPreferencesPlugin| and should call the parent class start method in its own
start method. Second all members which should be saved should be
tagged with the 'pref' metadata (use the tag method). The value of the
metadata can be `True` or any of the values presented in :ref: TODO. All value thus
tagged are loaded from the preference file if found, and saved when the user
request to save the preferences. Finally, a |Preferences| object to the
'ecpy.app.preferences.plugin' extension point. A single |Preferences| object
can be contributed per plugin.

.. note::

    The preferences system saves object by writing their repr to a file so any
    object whose repr can be evaluated by literal_eval can be saved
    (literal_eval is used for security reasons).

A |Preferences| object has the following members :

- 'auto_save': list of the names of members whose update should trigger an
  automatic saving of the preferences.
- 'edit_view': an enaml Container used to edit the preferences of the plugin.
  If no such object is conytributed the default templating mechanism presented
  below is used.
- 'saving_method': name of the plugin method to use to retrieve the values of
  the members which should be saved.
- 'loading_method': name of the plugin method to use to update the values of
  the saved members.

A |Preferences| object can be left blank as the default values are fine most of
the time.

Editing preferences object
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. todo:: write once implemented


Declaring error handlers
------------------------

During the application lifetime errors can occurs and the user needs to be
informed about them. Ecpy provides a command to do so 'ecpy.app.errors.signal'.
This command expects a 'kind' keyword specifying which handler to use to for
reporting this error. The selected handler determine the expected keywords.

By default Ecpy provides the following handlers, which displays the error and
log it:

- 'error' : To report an error which does not deserve a more complex handler.
  It expects a single 'message' keyword.
- 'extensions' : To report an error related to the loading of an extension.
  It expects a 'point' keyword referring to the extension point where the error
  occurred, and an 'infos' dictionary describing the issues that occurred.

In some situations, it is desirable to wait before reporting errors that the
execution of some code completed. To this effect the error plugin provides
the 'ecpy.app.errors.enter_error_gathering' which will hold the processing
of the errors till 'ecpy.app.errors.exit_error_gathering' is called.

Plugins can contribute new error handler to the 'ecpy.app.error.handler'
extension point. The contribution should be an |ErrorHandler| object.

An |ErrorHandler| needs to declare :

- 'id ': a unique id which will be used as 'kind' when calling
  'ecpy.app.errors.signal'
- 'handler' : a method handling the error. Note that to deal with error
  gathering it must be able to handle list of dictionary and not only
  dictionary. The handler shoudl log that an error occurred and return a widget
  to be displayed if it makes sense.
- 'report' : a method which should provide a summary of the errors that
  occurred it is meaningful.

.. note::
    As using this mechanism will cause a window to be displayed for the user
    sakes these commands should be called only from function/methods directly
    invoked at the level of the GUI.

Declaring dependencies
----------------------

When loading and transferring complex object over the network Ecpy needs to
collect all the base classes needed for reconstructing the object in an
environment lacking an active workbench. These are considered to be
build dependencies. In the same way some resources can be necessary to execute
some part of the application and need to be queried beforehand to allow the
system to run in a situation where the workbench is absent. Those are
considered to be run-time dependencies.

If your plugin introduces a new type of object which can, for example, be used
in tasks either as a build or as a runtime dependency you need to contribute
either a |BuildDependency| object to the 'ecpy.app.dependencies.build'
extension point or a |RuntimeDependecyCollector| object to the
'ecpy.app.dependencies.runtime_collect' extension point. In the case of
runtime dependencies, the collector is not responsible for the analysis of the
dependencies of an object this is left to an associated
|RuntimeDependecyAnalyser|, which allow to use the same kind of dependeny in
object with totally different structures and for which the same scheme of
analysis cannot be used. |RuntimeDependecyAnalyser| can be contributed to the
'ecpy.app.dependencies.runtime_analyse' extension point.

After analyses dependencies are stored into dedicated container class. Those
containers can then be used to request the identified dependencies. Once again
the same kind of container is returned which store the dependencies as a nested
dict in its 'dependencies' member. The top level of that dict corresponds to
the id of the dependency collector. Under each collector id the dependencies
are stored simply by id.

.. note::

    An object introducing a new kind of build dependency should have a dep_type
    attribute which should be an atom.Constant and which must be saved if the
    object can be saved under the .ini format.

A |BuildDependency| needs:

- an 'id' which must be unique and must match the name used for dep_type
  attribute value of the object this dependency collector is meant to act on.
- 'analyse': a method used to determine the dependencies of the object under
  scrutiny. Build dependencies should be added to the dependencies dictionary
  and runtime dependencies analysers ids should be returned (they will be
  called by the framework at a later time).
- 'validate': a method checking that all dependencies corresponding to this
  collector can be collected (they exist).
- 'collect': a method collecting the build dependencies previously identified
  by the analyse method.

A |RuntimeDependecyCollector| needs:

- an 'id' which must be unique.
- 'validate': a method checking that all dependencies corresponding to this
  collector can be collected (they exist).
- 'collect': a method getting the runtime dependencies previously identified by
  the analyse method. This method should request the privilege to use the
  dependencies if it makes sense.

A |RuntimeDependencyAnalyser| needs:

- an 'id' which must be unique.
- a 'collector_id' which should match a declared RuntimeDependencyCollector id.
- 'analyse': a method used to determine the runtime dependencies of the object
  under scrutiny. The dependencies should not be collected.

Please refer to the API documentation for more details about those objects and
the signature of the methods that need to be implemented.


Customizing logging
-------------------

By default Ecpy use two logs:

- a log collecting all levels and directed to a file (in the application folder
  under logs) and which is rotated daily or every time the application starts.
- a log collecting INFO log and above and stored in a string with a max of 1000
  lines. This string is meant to be used for displaying the log in the GUI, and
  is available from the state of the log plugin ('ecpy.app.logging').

If you need to add handlers, formatters or filters, you should do so in the
|Plugin.start| method of your plugin by calling the corresponding commands
(found in |LogManifest|).


Contributing to the application interface
-----------------------------------------

Adding entries in the main window menu bar
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plugins can also add new entries to the menu bar of the application main
window. To do so they should contribute |MenuItem| and |ActionItem| to the
'enaml.workbench.ui' plugin.

Providing new workspaces
^^^^^^^^^^^^^^^^^^^^^^^^

.. todo:: write
