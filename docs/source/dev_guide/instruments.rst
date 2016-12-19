.. _dev_instruments:

.. include:: ../substitutions.sub

Instruments
===========

Ecpy is designed to run physics experiments and such experiments requires more
than just a computer. One can need to apply a DC voltage, measure a current,
... All this requires instruments that needs to be interfaced and controlled.

The following sections will dicsuss how Ecpy handles instruments, but not how
to write drivers as Ecpy let the user free to use the framework of its choice
to do this.

.. contents::

Instruments within Ecpy
-----------------------

Instruments in Ecpy are managed by a dedicated plugin ensuring that a single
part of the application use a given instrument at any time, in order to avoid
conflict. Before using an instrument, the plugin planning to use the instrument
needs to request the right to do so. This right can be refused if another part
of the application, that cannot stop using it, is currently using it. Only
plugin which declare that they use instrument can request the right to use one.
See the :ref:`reg_user` section, to know how to declare that a plugin is an
instrument user.

When the privilege to use an instrument is granted, the instrument plugin
send back the 'profile' of the instrument. The profile of an instrument holds
all the information relative to how to proceed to open the connection to that
instrument :

- model_id : the instrument model which allow to determine to what kind of
  instrument this profile can be used to connect to.
- connections : information such as the VISA address of the instrument, or any
  other kind of way to identify the instrument when opening the connection.
  As often an instrument can be adressed through different protocols (GPIB,
  USB, ...), the profile regroup all those, so that the unicity of access can
  be guaranteed.
- settings : information specific for the driver that one wants to use to
  establish the connection. For example PyVISA, allows to select between
  different backends, and the driver could pass that information along.

.. note::

    A connection is mandatory to start a driver but the settings can be
    ignored.

All those parameters are stored in '.instr.ini' file that can be edited through
the GUI. It is hence necessary to add to Ecpy the proper widget to edit the
connections and settings (in the following those terms will often refer to
the widget rather than the data in the profile).
Settings are quite specific to the 'architecture' of the driver and this is
fine, however connections are not : the VISA address of an instrument does not
depend on the driver architecture. Hence connections should not be designed
with a particular architecture of driver in mind.
However not all driver 'architectures' use the same procedure to initialize a
driver and later on close the connection. Ecpy allows for such discrepencies
using starters. Starters are simply intermediate taking the driver class, the
connection and settings to use and taking care of the
initialization/finalization.

The following section will treat how to register a new driver (which should be
enough in most cases), a new instrument user, a new starter, a new connection,
and a new settings.

.. note::

    When writing a task using an instrument, one does not have to worry about
    the profile selection and the proper use of the starter as the provided
    |InstrumentTask| and |InstrTaskView| takes care of it.


Registering a driver
--------------------

Registering a driver is the most current operation of the ones presented. To do
so you need to do is to declare your driver in a plugin manifest so
that the main application can find it. Your plugin should contribute
an extension to 'ecpy.instruments.drivers' providing |Drivers| and/or |Driver|
objects.

Let's say we need to declare a single driver named 'MyDriver'. The name of our
extension package (see :doc:`glossary`) is named 'my_ecpy_plugin'.
Let's look at the example below:

.. code-block:: enaml

    enamldef MyPluginManifest(PluginManifest):

        id = 'my_plugin_id'

        Extension:
            point = 'ecpy.instruments.drivers'

            Drivers:
                path = 'my_ecpy_plugin'
                manufacturer = 'MyManufacturer'

                Driver:
                    driver = 'my_driver:MyDriver'
                    architecture = 'MyArchitecture'
                    model = 'MyModel'
                    kind = 'DC source'
                    starter = 'my_starter_id'
                    connections = {'VisaTCPIP': {'resource_class': 'SOCKET',
                                                 'port': 10000},
                                   'VisaUSB': {'resource_class': 'INSTR',
                                               'manufacturer_ID': '0xB49',
                                               'model_code': '0x46'}
                                   }

We declare a single child for the extension a |Drivers| object. |Drivers| does
nothing by themselves they are simply container for grouping drivers
declarations. They can be nested to any level. They have the following
attributes which, all save path, are also present in Driver. The values stored
will be accessed if Driver does not provide a value for a specific field :

- 'path': when declaring a driver you must specify in which module it is
  defined as a '.' sperated path. When declaring a path in a |Drivers| it will
  be prepended to any path-like declaration in all children.
- 'architecture': the architecture of all children drivers. For example if you
  are using the Lantz framework to write your drivers, write 'Lantz'. This name
  will be used when multiple drivers are available for the same model of
  instruments.
- 'manufacturer': the manucfacturer of all children drivers.
  For example : Keysight (please note that for manufacturer like Keysight,
  whose name changed through time aliases can be declared :ref:`decl_alias`,
  in those cases the name used internally will always be the main name.)
- 'serie': some instruments exists within a serie of similar instruments, and
  the serie might be more descriptive than the model (example : Keysight EXG,
  MXG, and EXG microwave sources). For such instruments the serie field should
  set.
- 'kind': the kind of instrument. Allowed values are : 'Other', 'DC source',
  'AWG', 'RF source', 'Lock-in', 'Spectrum analyser', 'Multimeter'.
  Those values are defined in 'ecpy.instruments.infos'. This is used only for
  filtering so this field is not mandatory.
- 'starter': Id of the starter to use with this driver.
- 'connections': Ids and default values for the supported connections (the
  meaningful default values should be documented by the connections).
- 'settings': Ids and default values for the supported settings (the
  meaningful default values should be documented by the settings).

We then declare our driver using a |Driver| object. A |Driver| has two
additional attributes compared to the one mentionned for |Drivers| :

- 'driver': this is the path ('.' separated) to the module defining the driver.
  The actual name of the driver is specified after a colon (':'). As mentioned
  above the path of all parent |Drivers| is preprended to this path.
- 'model': the model of instrument this driver has been written for. If a
  driver matches several models (which is unlikely as there are always some
  differences) it should be declared twice.

This is it. Now when starting Ecpy your new driver should be listed and if not
driver was previously declared for this model of instrument the model should
have been added.

.. warning ::

    The spelling of manufacturer, serie, model, architecture should be
    consistent. So do not use abbreviated names and always start the name by a
    capital letter. Look at existing code and contact the maintainers in cases
    of doubt.

.. note ::

    A driver is identified by its origin package, its architecture and the
    class name. <origin_package>.<architecture>.<class_name>


.. _reg_user:

Registering a user
------------------

As explained in the beginning only declared users can request the use of
instruments. This is so because the manager needs to know whether or not the
user is susceptible to stop using a driver if requested (and how to send it
such a request).

Declaring an instrument user is straightforward. To do so, you must contribute
an |InstrUser| object to the 'ecpy.instruments.users' extension point.
An |InstrUser| must have :

- an 'id' which should be unique and is generally the id of the plugin using
  instruments
- a 'policy' which is either 'releasable' or 'unreleasable' depending on
  whether the user can accept to relinquish the use of an instrument if asked.
- a 'release_profiles' declarative function which should be overridden if the
  policy is 'releasable'.


Registering a starter
---------------------

The goal of starters is to allow a transparent use of instrument no matter
their architecture. To declare a starter, you must contribute a |Starter|
object to the 'ecpy.instruments.starters' extension point.
A |Starter| must declare :

- an 'id' which should be unique and is the one used when declaring a driver.
- a 'description' detailing with what kind of driver this starter should be
  used.
- a 'starter' which should an instance of a subclass of |BaseStarter| and
  implement the following methods.

Methods of |BaseStarter| :

- a 'start' declarative function in charge of starting a driver. The
  driver returned should be ready for communication.
- a 'stop' declarative function responsible for cleanly closing the
  communication.
- a 'check_infos' declarative function used to test that a combination of
  (driver, connection, settings) does allow to open a connection. This method
  should not raise.
- a 'reset' declarative function responsible for resetting the driver after
  a suspected modification by the user.


Registering a connection
------------------------

As previously explained, the fields of a connection should be mapped to real
protocol used for communication and not a specific implementation. Hence the
VISA connections provided in Ecpy should cover most usages. However it is
possible to add other connections to cover less frequent cases.

To do so, you must contribute a |Connection| object to the
'ecpy.instruments.connections' extension point. A |Connection| must declare :

- an 'id' which should be unique and is the one used when declaring a driver.
- a 'description' detailing the possible default values that can be specified
  when declaring a driver.
- an 'new' declarative function which should create a new widget (inheriting
  from |BaseConnection|) used to edit the connection data. The 'defaults'
  dictionary should be used to properly initialize the widget. Note that all
  values should be expected as strings. The 'read_only' attributes should be
  set after creation to avoid trouble (hence you should use << when reading
  this attribute value in the view).


Registering a settings
----------------------

Contrary to connections settings are much more closely tied to a particular
architecture of driver. To declare a new settings, you must contribute a
|Settings| object to the 'ecpy.instruments.settings' extension point. A
|Settings| must declare :

- an 'id' which should be unique and is the one used when declaring a driver.
- a 'description' detailing the possible default values that can be specified
  when declaring a driver.
- an 'new' declarative function which should create a new widget (inheriting
  from |BaseSettings|) used to edit the settings data. The 'defaults'
  dictionary should be used to properly initialize the widget. Note that all
  values should be expected as strings. The 'read_only attributes should be
  set after creation to avoid trouble (hence you should use << when reading
  this attribute value in the view).


.. _decl_alias:

Registering a manufacturer alias
--------------------------------

Some instruments' manufacturer changed name during their history, and hence
the same instrument can be attributed to two different manufacturers. To deal
with that kind of cases, Ecpy allows to declare aliases to a manufacturer name.
When such aliases are declared, any alias can be used when declaring the driver
but only the 'real' name will be used internally (in profile for example).

To declare a manufacturer alias, you must contribute a |ManufacturerAlias| to
the 'ecpy.instruments.manufacturer_aliases' extension point. A
|ManufacturerAlias| must declare :

- an 'id' which should be the real manufacturer name.
- an 'aliases' list.


Manufacturer names (real and aliases) should all be capitalized.

.. note::

    The 'trivial' case of Keysight/Agilent/HP is already taken care of in Ecpy.