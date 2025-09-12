r"""This module provides common adsorbate structures.

Adsorbates can be retrieved using the :func:`get_adsorbate` function
or from any one of the subset dictionaries (:data:`CO2RR_ADSORBATES`,
:data:`NRR_ADSORBATES`, :data:`ORR_ADSORBATES`, :data:`HER_ADSORBATES`, or
:data:`ALL_ADSORBATES`).

|CO2RR| Intermediates from Nitopi et al. [1]_

NRR/UOR Intermediates Wan et al. [2]_ and Li et al. [3]_

Bond lengths, angles and positions from NIST_.

Example:
    >>> from ccu.adsorption.adsorbates import get_adsorbate
    >>> co2 = get_adsorbate("CO2")
    >>> co2
    Atoms(symbols='CO2', pbc=False)
    >>> co2.info["structure"]
    'CO2'
    >>> nho = get_adsorbate("NHO")
    >>> nho
    Atoms(symbols='HNO', pbc=False)
    >>> nho.info["structure"]
    'NHO'

References:

    .. [1] |ref1|_
    .. |ref1| replace:: Chem. Rev. **2019**, 119, 12, 7610-7672.
    .. _ref1: https://pubs.acs.org/doi/10.1021/acs.chemrev.8b00705
    .. [2] |ref2|_
    .. |ref2| replace:: ACS Catal. **2023**, 13, 3, 1926-1933.
    .. _ref2: https://pubs.acs.org/doi/abs/10.1021/acscatal.2c05315
    .. [3] |ref3|_
    .. |ref3| replace:: Angew. Chem. Int. Ed. **2021**, 60, 51, 26656.
    .. _ref3: https://onlinelibrary.wiley.com/doi/abs/10.1002/anie.202107886
    .. _NIST: https://cccbdb.nist.gov
"""

import logging

import ase
from ase.atoms import Atoms
from ase.build import molecule

logger = logging.getLogger(__name__)


def _co2rr_adsorbates() -> dict[str, Atoms]:
    co2 = molecule("CO2")

    # C-O: HCOOH; C=0: HCOOH, O-H: HCOOH
    cooh_cis = Atoms(
        "CO2H",
        positions=[[0, 0, 0], [1.202, 0, 0], [0, 1.343, 0], [0.972, 1.343, 0]],
    )
    # <OCO: HCOOH
    cooh_cis.set_angle(2, 0, 1, angle=124.9)
    # <COH: HCOOH
    cooh_cis.set_angle(0, 2, 3, angle=106.3)
    cooh_cis.info["special_centers"] = (0,)

    cooh = cooh_trans = Atoms(
        "CO2H",
        positions=[
            [0, 0, 0],
            [1.202, 0, 0],
            [0, 1.343, 0],
            [-0.972, 1.343, 0],
        ],
    )
    # <OCO: HCOOH
    cooh_trans.set_angle(2, 0, 1, angle=124.9)
    # <COH: HCOOH (flipped)
    cooh_trans.set_angle(0, 2, 3, angle=106.3)
    cooh_trans.info["special_centers"] = (0,)

    # C-O: HCOOH; C-H: HCOOH
    ocho = Atoms(
        "CO2H",
        positions=[[0, 0, 0], [1.343, 0, 0], [0, 1.343, 0], [-1.097, 0, 0]],
    )
    # <OCO: symmetry
    ocho.set_angle(2, 0, 1, angle=120)
    # <COH: HCOOH
    ocho.set_angle(1, 0, 3, angle=120)
    ocho.info["special_centers"] = (0,)

    hcooh = molecule("HCOOH")
    hcooh.info["special_centers"] = (1,)

    co = Atoms("CO", positions=[[0, 0, 0], [1.128, 0, 0]])

    # C-O: CH3OH; O-H: CH3OH
    coh = Atoms("COH", positions=[[0, 0, 0], [1.427, 0, 0], [0, 0.956, 0]])
    # <COH: CH3OH
    coh.set_angle(1, 0, 2, angle=108.87)
    coh.info["special_centers"] = (0,)

    # C-H: CHO; C-O: CHO
    cho = Atoms("CHO", positions=[[0, 0, 0], [1.080, 0, 0], [0, 1.198, 0]])
    # <HCO: CHO
    cho.set_angle(1, 0, 2, angle=119.5)
    cho.info["special_centers"] = (0,)

    c = Atoms("C", positions=[[0, 0, 0]])

    # C-H: HCOOH; C-O: HCOOH; O-H: HCOOH
    choh = Atoms(
        "CHOH",
        positions=[
            [0, 0, 0],
            [0, -1.097, 0],
            [1.343, 0, 0],
            [1.343, 0.972, 0],
        ],
    )
    # <OCO: HCOOH
    choh.set_angle(1, 0, 2, angle=128.8)
    # <COH: HCOOH
    choh.set_angle(0, 2, 3, angle=106.3)
    choh.info["special_centers"] = (0,)

    # C-H: H2CO; C-O: H2CO
    ch2o = Atoms(
        "CH2O",
        positions=[[0, 0, 0], [0, -1.111, 0], [1.111, 0, 0], [0, 1.205, 0]],
    )
    # <HCH: H2CO
    ch2o.set_angle(2, 0, 1, angle=116.133)
    # <HCO: H2CO
    ch2o.set_angle(1, 0, 3, angle=121.9)
    ch2o.info["special_centers"] = (0,)

    # C-H: CH3OH; C-O: CH3OH; O-H: CH3OH
    ch2oh = Atoms(
        "CH2OH",
        positions=[
            [0, 0, 0],
            [-1.096, 0, 0],
            [0, -1.096, 0],
            [1.427, 0, 0],
            [1.427, 0.956, 0],
        ],
    )
    # <HCH: H2CO
    ch2oh.set_angle(2, 0, 1, angle=116.133)
    # <HCO: symmetry
    ch2oh.set_angle(1, 0, 3, angle=121.9)
    # <HOC: CH3OH
    ch2oh.set_angle(0, 3, 4, angle=108.87)
    ch2oh.info["special_centers"] = (0,)

    # Positions from CH3O
    och3 = Atoms(
        "OCH3",
        positions=[
            [0, 0, 0.8151],
            [0, 0, -0.5899],
            [0, 1.0360, -0.9938],
            [0.8972, -0.5180, -0.9938],
            [-0.8972, -0.5180, -0.9938],
        ],
    )
    och3.info["special_centers"] = (0,)

    # C-H: H2CO
    ch2 = Atoms("CH2", positions=[[0, 0, 0], [0, -1.111, 0], [1.111, 0, 0]])
    # <HCH: H2CO
    ch2.set_angle(1, 0, 2, angle=116.133)
    ch2.info["special_centers"] = (0,)

    # Positions from CH3O
    ch3 = Atoms(
        "CH3",
        positions=[
            [0, 0, -0.5899],
            [0, 1.0360, -0.9938],
            [0.8972, -0.5180, -0.9938],
            [-0.8972, -0.5180, -0.9938],
        ],
    )
    ch3.info["special_centers"] = (0,)
    return {
        "CO2": co2,
        "COOH_CIS": cooh_cis,
        "COOH_TRANS": cooh_trans,
        # The default COOH is trans
        "COOH": cooh,
        "OCHO": ocho,
        "HCOOH": hcooh,
        "CO": co,
        "COH": coh,
        "CHO": cho,
        "C": c,
        "CHOH": choh,
        "CH2O": ch2o,
        "HC2OH": ch2oh,
        "OCH3": och3,
        "CH2": ch2,
        "CH3": ch3,
    }


def _nrr_adsorbates() -> dict[str, Atoms]:
    # N-O: NO3
    no3 = Atoms(
        "NO3",
        positions=[[0, 0, 0], [0, 1.238, 0], [-1.238, 0, 0], [1.238, 0, 0]],
    )
    # <ONO: NO3
    no3.set_angle(2, 0, 1, angle=120)
    no3.set_angle(1, 0, 3, angle=120)

    # From pubchem (cid=944)
    no3h = Atoms(
        "NO3H",
        positions=[
            [-4.1600e-02, -1.3017e00, 1.0000e-04],
            [-1.1005e00, 6.3770e-01, 1.0000e-04],
            [1.1387e00, 5.6850e-01, 1.0000e-04],
            [3.4000e-03, 9.5600e-02, -4.0000e-04],
            [9.0950e-01, -1.5016e00, 2.0000e-04],
        ],
    )
    no3h.info["special_centers"] = (3,)

    # N-O: HNO2
    no2 = Atoms("NO2", positions=[[0, 0, 0], [0, 1.442, 0], [1.442, 0, 0]])
    # <ONO: HNO2
    no2.set_angle(1, 0, 2, angle=110.6)

    # N-O: HNO2; N=0: HNO2
    no2h = Atoms(
        "NO2H",
        positions=[
            [0, 0, 0],
            [-1.442, 0, 0],
            [0, 1.169, 0],
            [-1.442, -0.959, 0],
        ],
    )
    # <ONO: HNO2
    no2h.set_angle(1, 0, 2, angle=110.6)
    # <HON: HNO2
    no2h.set_angle(0, 1, 3, angle=102.1)
    no2h.info["special_centers"] = (0,)

    # N=O: NO
    no = Atoms("NO", positions=[[0, 0, 0], [1.154, 0, 0]])

    # N-O: HNO2 & NH2OH (average); O-H: HNO2 & NH2OH (average)
    noh = Atoms(
        "NOH",
        positions=[
            [0, 0, 0],
            [0.5 * (1.442 + 1.453), 0, 0],
            [0.5 * (1.442 + 1.453), 0.5 * (0.959 + 0.962), 0],
        ],
    )
    # <NOH: HNO2 & NH2OH (average)
    noh.set_angle(0, 1, 2, angle=0.5 * (102.1 + 101.37))
    noh.info["special_centers"] = (0,)

    # N-H: NH2OH & HNO (average); N-O: NH2OH & HNO (average)
    nho = Atoms(
        "HNO",
        positions=[
            [0, 0, 0],
            [0.5 * (1.016 + 1.090), 0, 0],
            [0.5 * (1.016 + 1.090), 0.5 * (1.453 + 1.209), 0],
        ],
    )
    # <HNO: NH2OH & HNO (average)
    nho.set_angle(0, 1, 2, angle=0.5 * (107.01 + 108.047))
    nho.info["special_centers"] = (2,)

    # N-H: NH2OH; N-O: NH2OH; O-H: NH2OH
    nhoh = Atoms(
        "HNOH",
        positions=[
            [0, 0, 0],
            [1.016, 0, 0],
            [1.016, 1.453, 0],
            [1.016 + 0.962, 1.453, 0],
        ],
    )
    # <HNO: NH2OH
    nhoh.set_angle(0, 1, 2, angle=107.1)
    # <HON: NH2OH
    nhoh.set_angle(1, 2, 3, angle=101.37)
    nhoh.info["special_centers"] = (1,)

    n = Atoms("N")

    # N-H: NH
    nh = Atoms("NH", positions=[[0, 0, 0], [1.036, 0, 0]])

    # N-H: NH2
    nh2 = ase.Atoms(
        "HNH",
        positions=[
            [0, 0, 0],
            [1.024, 0, 0],
            [0, 1.024, 0],
        ],
    )
    # <HNH: NH2
    nh2.set_angle(0, 1, 2, angle=103.4)

    # N-H: NH2; N-O: NH2OH
    nh2o = ase.Atoms(
        "NH2O",
        positions=[
            [0, 0, 0],
            [1.024, 0, 0],
            [0, 1.024, 0],
            [-0.8523, -0.8523, 0],
        ],
    )
    nh2o.info["special_centers"] = (
        0,
        3,
    )

    # N-H: NH2OH
    nh2oh = ase.Atoms(
        "NH2OH",
        positions=[
            [-0.0094, 0.704, 0],
            [0.5469, 1.0012, 0.7965],
            [0.5469, 1.0012, -0.7965],
            [-0.0094, -0.7490, 0],
            [-0.9525, -0.9386, 0],
        ],
    )
    nh2oh.info["special_centers"] = (
        0,
        3,
    )

    # Positions from NH3
    nh3 = Atoms(
        "NH3",
        positions=[
            [0, 0, 0],
            [0, -0.9377, -0.3816],
            [0.812, 0.4689, -0.3816],
            [-0.812, 0.4689, -0.3816],
        ],
    )

    n2 = molecule("N2")
    n2o = molecule("N2O")

    return {
        "NO3": no3,
        "NO3H": no3h,
        "NO2": no2,
        "NO2H": no2h,
        "NO": no,
        "NOH": noh,
        "NHO": nho,
        "NHOH": nhoh,
        "N": n,
        "NH": nh,
        "NH2": nh2,
        "NH2O": nh2o,
        "NH2OH": nh2oh,
        "NH3": nh3,
        "N2": n2,
        "N2O": n2o,
    }


def _orr_adsorbates() -> dict[str, Atoms]:
    return {
        "O": Atoms("O"),
        # O-H: OH-
        "OH": Atoms("OH", positions=[[0, 0, 0], [0.964, 0, 0]]),
        "H2O": molecule("H2O"),
    }


#: adsorbates for the carbon dioxide reduction reaction
#: Note that COOH is an alias for COOH_TRANS
CO2RR_ADSORBATES = _co2rr_adsorbates()


#: adsorbates for the urea oxidation and nitrate reduction reactions
NRR_ADSORBATES = _nrr_adsorbates()


#: adsorbates for the oxygen reduction and evolution reactions
ORR_ADSORBATES = _orr_adsorbates()


#: adsorbates for the hydrogen evolution reaction
HER_ADSORBATES = {
    "H": Atoms("H"),
    "OH": ORR_ADSORBATES["OH"],
    "H2O": ORR_ADSORBATES["H2O"],
}


#: All internally defined adsorbates
ALL_ADSORBATES: dict[str, Atoms] = {}
ALL_ADSORBATES.update(CO2RR_ADSORBATES)
ALL_ADSORBATES.update(NRR_ADSORBATES)
ALL_ADSORBATES.update(ORR_ADSORBATES)
ALL_ADSORBATES.update(HER_ADSORBATES)

for name, adsorbate in ALL_ADSORBATES.items():
    adsorbate.info["structure"] = name


def get_adsorbate(adsorbate: str) -> Atoms:
    """Retrieve the requested adsorbate from `ase` or the internal database.

    Args:
        adsorbate: The name of the adsorbate to retrieve.

    Returns:
        An :class:`~ase.Atoms` instance representing the requested adsorbate.

    Raises:
        NotImplementedError: The requested adsorbate is neither a molecule
            supported by ASE nor a defined adsorbate in
            :mod:`ccu.adsorption.adsorbates`.

    Note:
        The name of the adsorbate will be stored under the `"structure"` key
        of its `info` dictionary.

    .. seealso:: :func:`ase.build.molecule`
    """
    name = adsorbate.upper()
    try:
        atoms = molecule(name)
        atoms.info["structure"] = name
        return atoms
    except KeyError:
        pass

    try:
        return ALL_ADSORBATES[name]
    except KeyError as error:
        msg = f"The {adsorbate} adsorbate is not supported yet."
        raise NotImplementedError(msg) from error
