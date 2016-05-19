.. _dev_guide:

Extending Ecpy
==============

Ecpy is designed with the idea that user should be able to extend it to fit
their own needs. The following section will describe how one should proceed to
do so. The three first sections describe general concepts which are always
applicable, the following ones are dedicated to the extension of specific part
of the application.

If you need to extend the functionalities provided by an extension package
please refer to its documentation for the specifics of the procedure.

.. toctree::
    :numbered:
    :maxdepth: 2

    glossary
    application
    tasks
    instruments
    measure
    testing
    style_guide
    atom_enaml

.. note::

   When writing code for Ecpy, or an extension packages you should follow the
   project style guides described in :doc:`style_guide`. Of course if you are
   developing a private extension you are free to do as you see fit but in
   order for a contribution to Ecpy or one of its official extension package
   to be accepted it must follow those style guides.

.. note::

    Ecpy does not export any name in the \_\_init\_\_.py module. However for 
    ease of use the objects necessary to extend Ecpy functionality are exported
    in the api.py file associated with each plugin.
   
.. note::

    Ecpy is built on top of Atom and Enaml. Please have a look at
    :doc:`atom_enaml` for an explanation on how this influence the code.
