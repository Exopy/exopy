.. _dev_tasks:

.. include:: substitutions.rst

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
database. Those values can also be during the edition of the task parameters 
through its view by **assigning** a new dictionary to task_database_entries.

.. code-block:: python 
	from atom.api import set_default

	class MyTask(SimpleTask):
		"""MyTask description.
		
		"""
		task_database_entries = set_default({'val': 1})
		
The actual description of what the task is meant to do is contained in the 
perform method and it is the one you need to override (save when writing an 
interfaceable task see next section). This method take either no argument, or a
single keyword argument if it can be used inside a loop in which case the 
argument will be the current value of the loop. Below is a list of some useful
methods you might need :
- |write_in_database| :
- |format_string|:
- |format_and_eval_string|:

According to whether the formula is meant to be evaluated or simply formatted
(ie generate a string) the member should be tagged with 'feval' or 'fmt' (value
should be True). This tag alllow to automat


When to use interfaces
^^^^^^^^^^^^^^^^^^^^^^


Creating the view
^^^^^^^^^^^^^^^^^


Registering your task
^^^^^^^^^^^^^^^^^^^^^


Creating a new interfaces
-------------------------


Minimal methods to implement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


When to use interfaces
^^^^^^^^^^^^^^^^^^^^^^


Creating the view
^^^^^^^^^^^^^^^^^


Registering your interface
^^^^^^^^^^^^^^^^^^^^^^^^^^


