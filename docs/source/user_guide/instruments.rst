.. _instruments:

Instruments
===========

Instruments are at the root of every physical measurement. In order for Exopy to
be able to work with an instrument, it needs :

- a driver, which is the layer responsible for transferring the instruction 
  from the program to the instrument and can be written using the VISA protocol
  or a custom DLL.
- enough information to open the communication with the instrument (we will call
  those information the profile of the instrument).
 
Assuming that somebody wrote the driver for the instrument all you will have
to do will be to provide the information needed by the profile. The next 
sections will explain you how to provide those informations and how Exopy
manages them.

.. contents::

Creating an instrument profile
------------------------------

All informations related to the instruments can be accessed through the 
'Tools/Instruments/Open browser' menu. This is where you need to go to add 
profiles.

This will open a dialog holding different tabs :

- The first one is used to manage the instrument profile and will be discussed
  in details in this section.
- The second one displays the current use of the profiles and allow you to track
  what part of the application is currently using the instruments.
- The third one simply allows you to check the known drivers.

The first tab holds the list of the known profiles, which is of course empty to
begin with. Afterwards selecting a profile will display a summary of the 
information stored in the profile, which can be edited or deleted using the
so named buttons below the summary. To add a profile you should use the 'Add'
button, which opens another dialog.

A profile contains different pieces of information :

- an id which allows you to identify the instrument when you need to select it.
- the model of the instrument this profile corresponds to.
- the connection information (named connections) which are used to open the 
  connection. This typically contain the 'address' of the instrument. Note that
  you can have multiple valid connections for a single instrument if it 
  supports different protocols (for example a lot of modern VISA-based 
  instrument can be addressed either through USB or TCPIP).
- the settings which allow you to pass additional parameters to the driver.
  Specifying settings is fully optional and depends on the architecture of the 
  driver.
  
First you should fill in the id, and select the model of the instrument. To do
so use the 'Select' button to open yet another dialog. This dialog presents the 
the known instruments models as tree where the model are grouped by 
manufacturer (and serie if the model is part of a serie). To find the model you
are looking for more quickly, you can also filter based on the type of 
instrument (you can for example display only the DC sources). When selecting a 
model the right panel will display more information such as the drivers that 
can be used and the allowed connections and settings (note that not all 
connections and settings apply to all drivers).

Once you have selected the model, you will be able to add connections and 
settings. You can add at most one connection for each supported connection type
(a connection type is considered supported if at least one driver supports it).
On the contrary, multiple settings of the same type can co-exist (they must 
have different names).

When adding a connection or settings, you are first prompted to choose one, and
given a brief description of each one. Once added you can select it and provide
the expected information.

.. note::

    For VISA connections, you should only have to provide the address as most
    other fields should be already pre-completed based on the infos provided
    by the drivers.
    
You are now done and can add the profile. But before doing so you may want to 
validate that the information you provided are correct. To do so click on
the 'Validate' button. A dialog will show. On this dialog, you should select 
the connection you want to test and if pertinent the driver and settings to use
for the test. Once this is done click on 'Test connection' (and wait). The 
result of the operation will be displayed in the field below.

Use of profiles
---------------

The second tab of the dialog allows to know what part of the application is 
currently using instruments. Note that currently only one part of the 
application can use instruments at any given time.

Typically when starting a measurement the instruments used in the measurement should
go from unused to used by the 'exopy.measurement' plugin.
