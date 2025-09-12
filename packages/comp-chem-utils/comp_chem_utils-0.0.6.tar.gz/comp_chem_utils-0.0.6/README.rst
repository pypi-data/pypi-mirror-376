=============
CompChemUtils
=============

|ccu|_ is a set of tools for computational chemistry workflows.

.. start

Install `ccu`
=============

`ccu` requires: Python_ 3.10+ or PyPy3.

1. Run the following command in your command line:

.. code-block::

    pip install comp-chem-utils

2. Check that you've installed the correct version:

.. code-block::

    $ ccu --version
    0.0.6

You can also install the in-development version with:

.. code-block::

    pip install git+ssh://git@gitlab.com/ugognw/python-comp-chem-utils.git@development

Usage
=====

Determine the symmetry of a water molecule
------------------------------------------

.. code-block:: python

    >>> from ase.build import molecule
    >>> from ccu.structure.axisfinder import find_secondary_axis
    >>> from ccu.structure.symmetry import Rotation, check_symmetry
    >>> h2o = molecule('H2O')
    >>> axis = find_secondary_axis(h2o)
    >>> r = Rotation(180, axis)
    >>> check_symmetry(r, h2o)
    True

Retrieve reaction intermediates for the two-electron |CO2| reduction reaction
-----------------------------------------------------------------------------

.. code-block:: python

    >>> from ccu.adsorption.adsorbates import get_adsorbate
    >>> cooh = get_adsorbate('COOH_CIS')
    >>> cooh.positions
    array([[ 0.        ,  0.        ,  0.        ],
           [ 0.98582255, -0.68771934,  0.        ],
           [ 0.        ,  1.343     ,  0.        ],
           [ 0.93293074,  1.61580804,  0.        ]])
    >>> ocho =  get_adsorbate('OCHO')
    >>> ocho.positions
    array([[ 0.        ,  0.        ,  0.        ],
           [ 1.16307212, -0.6715    ,  0.        ],
           [ 0.        ,  1.343     ,  0.        ],
           [-0.95002987, -0.5485    ,  0.        ]])

Place adsorbates on a surface
-----------------------------

Place adsorbates on a surface (namely, ``Cu-THQ.traj``) while considering the
symmetry of the adsorbate and the adsorption sites. ::

    ccu adsorb CO Cu-THQ.traj orientations/


.. |ccu| replace:: ``CompChemUtils``
.. _ccu: https://gitlab.com/ugognw/python-comp-chem-utils/
.. _Python: https://www.python.org
.. |click| replace:: ``click``
.. _click: https://click.palletsprojects.com/en/8.1.x/
.. |numpy| replace:: ``numpy``
.. _numpy: https://numpy.org
.. |scipy| replace:: ``scipy``
.. _scipy: https://scipy.org
.. |ase| replace:: ``ase``
.. _ASE: https://wiki.fysik.dtu.dk/ase/index.html
.. |CO2| replace:: CO\ :sub:`2`

.. end

Documentation
=============

View the latest version of the documentation on `Read the Docs`_

.. _Read the Docs: https://python-comp-chem-utils.readthedocs.io/en/latest
