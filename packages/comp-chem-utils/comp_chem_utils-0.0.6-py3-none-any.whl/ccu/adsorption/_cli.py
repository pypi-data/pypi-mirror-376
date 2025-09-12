"""CLI utilities for adsorption studies."""

from pathlib import Path
import sys
from typing import Any
from typing import Literal

from ase import collections
from ase.atoms import Atoms
from ase.build.molecule import extra
import click

from ccu.adsorption.adsorbates import ALL_ADSORBATES
from ccu.adsorption.complexes import DEFAULT_ADSORBATE_TAG
from ccu.adsorption.complexes import generate_complexes
from ccu.adsorption.complexes import write_complexes
from ccu.adsorption.sites import HubSpokeFinder
from ccu.adsorption.sites import Triangulator

_all_adsorbates = (
    list(ALL_ADSORBATES.keys()) + collections.g2.names + list(extra.keys())
)


def print_adsorbates(
    ctx: click.Context,  # noqa: ARG001
    value: Any,  # noqa: ARG001
    param: click.Parameter,
) -> None:
    "Print a list of all adsorbates available to ccu."
    if not param:
        return

    header = "AVAILABLE ADSORBATES"
    click.echo(header)
    source_names = ["ccu", "g2", "extra"]
    sources = [ALL_ADSORBATES, collections.g2.names, extra]
    width = len(header)

    def _print_header(text: str) -> None:
        return click.echo(text.center(width, "-"))

    for name, source in zip(source_names, sources, strict=False):
        _print_header(f" from {name} ")
        for adsorbate in source:
            click.echo(adsorbate)

    sys.exit(0)


@click.command(
    name="adsorb",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument(
    "adsorbate",
    type=click.Choice(_all_adsorbates, case_sensitive=False),
    required=True,
    metavar="ADSORBATE",
)
@click.argument(
    "structure",
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.argument(
    "destination",
    default=Path.cwd(),
    type=click.Path(file_okay=False, path_type=Path),
)
@click.option(
    "-t",
    "--adsorbate-tag",
    "--tag",
    default=DEFAULT_ADSORBATE_TAG,
    type=int,
    help="Specify an integer with which to tag adsorbate atoms.",
    show_default=True,
)
@click.option(
    "-s",
    "--separation",
    help=(
        "Specify the minimum distance between the surface and any adsorbate "
        "atom"
    ),
    default=1.8,
    type=float,
    show_default=True,
)
@click.option(
    "-c",
    "--centers",
    default="com",
    help=(
        "Specify a method of centering the adsorbate. 'special' will center "
        "adsorbates using the 'special_centers' key in the Atoms.info "
        "dictionary. 'all' will center adsorbates using their atomic "
        "coordinates. 'com' will center adsorbates by their center-of-mass."
    ),
    type=click.Choice(["special", "com", "all"], case_sensitive=False),
    show_default=True,
)
@click.option(
    "-f",
    "--finder",
    default="tri",
    help=(
        "Specify a site finder protocol. 'tri' will select the method "
        "implemented by ccu.adsorption.sites.Triangulator. 'hub' will "
        "select the method implemented by ccu.adsorption.sites.HubSpokeFinder "
    ),
    type=click.Choice(["tri", "hub"], case_sensitive=False),
    show_default=True,
)
@click.option(
    "--no-symmetry/--symmetry",
    " /-Y",
    "symmetry",
    default=False,
    help="Whether or not to ignore the symmetry of the adsorbate when "
    "constructing adsorbate complexes. '--no-symmetry' ignores "
    "symmetry. Symmetry is not considered by default.",
)
@click.option(
    "-l",
    "--list",
    help="List all available adsorbates",
    flag_value=True,
    is_flag=True,
    is_eager=True,
    callback=print_adsorbates,
    expose_value=False,
)
def main(
    adsorbate: str,
    structure: str | Path | Atoms,
    destination: Path,
    separation: float,
    centers: Literal["com", "special", "all"],
    finder: str,
    symmetry: bool,
    adsorbate_tag: int,
):
    """Create adsorbate complexes for a given structure.

    Each complex is written to a .traj file with identifying metadata
    about the adsorbate identity, orientation, site, and structure.

    ADSORBATE is the name of the adsorbate to place on the surface.

    STRUCTURE is the path to the surface on which the adsorbate will be placed.

    DESTINATION is the directory in which to write the .traj files. The
    directory is created if it does not exist. Defaults to the current
    working directory.
    """
    complexes = generate_complexes(
        structure=structure,
        adsorbate=adsorbate,
        separation=separation,
        centers=centers,
        symmetry=symmetry,
        finder=HubSpokeFinder() if finder == "hub" else Triangulator(),
        adsorbate_tag=adsorbate_tag,
    )
    write_complexes(complexes, destination)
    print(
        f"{len(complexes)} complexes created and written to directory: "
        + str(destination)
    )
