=========
Workflows
=========

`ccu` defines the following convenience functions to perform common
sets of calculations:

- :func:`ccu.workflows.hubbard_u.get_hubbard_u`: calculate the hubbard :math:`U`
  parameter from linear response theory by the method of Coccoccioni [CG05]_
- :func:`ccu.workflows.calculation.run_calculation`: perform a relaxation calculation
  and log energy and maximum forces after calculation
- :func:`ccu.workflows.vibration.run_vibration`: perform a vibrational calculation and
  log vibrations and thermodynamic quantities (thermal corrections and zero-
  point energy)
- :func:`ccu.workflows.infrared.run_infrared`: calculate the infrared spectra of a
  system and log frequencies, dipole moments, and zero-point energy
- :func:`ccu.workflows.vcdd.run_vcdd`: perform a series of calculations that can be used
  to generate valence charge density difference diagrams

.. [CG05] Cococcioni and de Gironcoli. Phys. Rev. B 71, 035105 (2005)
