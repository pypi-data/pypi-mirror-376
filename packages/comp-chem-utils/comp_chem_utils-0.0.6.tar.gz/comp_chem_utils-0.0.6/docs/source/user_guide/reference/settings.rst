Configuration Options
---------------------

.. automodule:: ccu.settings
   :members:
   :show-inheritance:
   :undoc-members:


.. _sample-config-file:

Sample Configuration File
===========================

The configuration file must be written in |toml|_. A sample configuration file
equivalent to the default settings can be seen below::

   # config.toml

   LOG_LEVEL = 10
   OUTPUT_ATOMS = final.traj

.. |toml| replace:: TOML
.. _toml: https://toml.io/en/
