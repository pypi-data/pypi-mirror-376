from ase.atoms import Atoms
from ase.build import fcc100
import numpy as np
import pytest

from ccu.adsorption.adsorbates import get_adsorbate
from ccu.adsorption.sites import HUB_TAG
from ccu.adsorption.sites import SPOKE_TAG
from ccu.adsorption.sites import AdsorptionSite
from ccu.adsorption.sites import SiteAlignment
from ccu.adsorption.sites import SiteFinder


@pytest.fixture(name="structure")
def fixture_structure() -> Atoms:
    structure = fcc100("Cu", (3, 3, 1))
    structure.center(vacuum=10, axis=2)
    structure.info["structure"] = "Cu(100)"
    return structure


@pytest.fixture(
    name="adsorbate",
    params=["H2", "CO", "CO2", "OH", "NHO", "COOH", "CH3", "NH2OH"],
)
def fixture_adsorbate(request) -> Atoms:
    return get_adsorbate(request.param)


@pytest.fixture(name="tag_structure")
def fixture_tag_structure(structure: Atoms) -> None:
    tags = [0] * len(structure)
    tags[4] = HUB_TAG
    tags[1] = tags[3] = tags[5] = tags[7] = SPOKE_TAG
    structure.set_tags(tags)


def finder(structure: Atoms) -> list[AdsorptionSite]:
    return [
        AdsorptionSite(
            position=structure[0].position,
            description=f"on {structure[0].symbol}",
            alignments=[SiteAlignment(np.array([1.0, 0.0, 0.0]), "x")],
            norm=np.array([0, 0.0, 1.0]),
        )
    ]


@pytest.fixture(name="site_finder")
def fixture_site_finder() -> SiteFinder:
    return finder


@pytest.fixture(name="sites")
def fixture_sites(
    site_finder: SiteFinder, structure: Atoms
) -> list[AdsorptionSite]:
    return site_finder(structure)
