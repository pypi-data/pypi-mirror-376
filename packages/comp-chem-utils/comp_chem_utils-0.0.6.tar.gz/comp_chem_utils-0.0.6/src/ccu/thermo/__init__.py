r"""Convenience functions for calculating thermodynamic quantities.

For a limited number of molecular species,
:mod:`ccu.thermo.chempot` provides vibrational zero-point
energies and a DFT-parametrized interpolation for chemical potentials between 0
and 1100 K. The parametrization is of the form:

.. math::
   :label: chem-pot

    \Delta \mu_{0 \rightarrow T} = b + m T + k_b T \log P

where :math:`T` and :math:`P` are temperature (in K) and pressure (in bar),
respectively, :math:`k_b` is the Boltzmann constant, and
:math:`b(T)` and :math:`m(T)` are parametrized functions of :math:`T`
that are unique to each molecule. These two datasets allow one to calculate
free energies at any given temperature between 1 and 1000K. That is, given
a chemical potential :math:`\Delta \mu` and vibrational zero-point energy
:math:`ZPE`, the free energy :math:`G` is given by

.. math::
   :label: gibbs-chem-pot

    G = \Delta \mu_{0 \rightarrow T} + ZPE
"""

from typing import NamedTuple


class _ThermodynamicState(NamedTuple):
    temperature: float = 273.15
    pressure: float = 1.0


# IUPAC Standard
STP = _ThermodynamicState()

WAVENUMBER_TO_EV = 0.0001239843
