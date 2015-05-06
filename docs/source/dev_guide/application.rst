.. _application:

.. include:: substitutions.rst

Interacting with the core of Ecpy
=================================

This section will focus on the functionality offered by the plugins 
constituting the core of the Ecpy application and how custom plugin can use
and or extend those functionalities.

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
  formatted as such (see :ref:`Style guidelines`).
  
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
   used for operations not fitting into the |start| and |stop| methods of the
   plugin. This fits operation that must be performed at application start up 
   and cannot be deferred to plugin starting, or clean up operations requiring
   the full application to be active (ie not dependent only on the plugin state
   )
   
Declaring an AppStartup extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Declaring an AppClosing extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Declaring an AppClosed extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   
Using the built in preferences manager
--------------------------------------



Declaring dependencies
----------------------


Customizing logging
-------------------


Contributing to the main window menu bar
----------------------------------------
