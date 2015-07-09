.. dev_atom_enaml::

Atom and Enaml
==============

Atom
----

Atom allow to create memory efficient python object by specifying in the class 
the members (rather than allowing dynamic attributes). Atom can also be used to
add type checking to object members. This goes against the notion of 
duck-typing but tends to make the code easier to read. Note also that metadata 
can be added to a member using the :py:meth:tag method. Metadata are 
extensively used in Ecpy.

.. note::
	
	For clarity sake and Python2/3 compatibility, Unicode should be used 
	instead of strings.

Enaml
-----

.. todo::
