"""Utilities for analyzing Bader charge data."""

import logging
from pathlib import Path
from typing import Any

import ase
import ase.io
import ase.io.bader
import click

logger = logging.getLogger(__name__)


class _AtomsType(click.ParamType):
    name = "atoms"

    def convert(self, value: Any, param, ctx):
        if isinstance(value, ase.Atoms):
            return value

        if not isinstance(value, str | Path):
            msg = f"Invalid type: {type(value)}"
            self.fail(msg, param, ctx)

        try:
            atoms = ase.io.read(value)
            return atoms if isinstance(atoms, ase.Atoms) else atoms[-1]
        except ValueError:
            msg = f"{value!r} cannot be read into an ase.Atoms object"
            self.fail(msg, param, ctx)


def _get_tag_indices(atoms: ase.Atoms) -> dict[int, list[int]]:
    """Group indices by tag on an ase.Atoms object.

    Args:
        atoms: An :class:`ase.atoms.Atoms` object.

    Returns:
        A dictionary mapping tag numbers to the indices of atoms with that tag
        number.

    """
    indices: dict[int, list[int]] = {}

    for i, atom in enumerate(atoms):
        if atom.tag in indices:
            indices[atom.tag].append(i)
        else:
            indices[atom.tag] = [i]

    return indices


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--atoms",
    help="A file from which an Atoms object can be read via ase.io.read.",
    type=_AtomsType(),
    required=True,
)
@click.option(
    "--smart-mode/--no-smart-mode",
    required=False,
    is_flag=True,
    default=False,
    help="This is a special mode that will print out cumulative Bader "
    "charges for each tag group in the format TAG: BADER_CHARGE "
    "where TAG is an integer used to tag atoms in an "
    "Atoms object and BADER_CHARGE is the sum of the "
    "Bader charge of all atoms with that tag. Note that if both "
    "--smart-mode and INDICES are specified, this option is "
    "ignored.",
)
@click.option(
    "--sort-file",
    help="Specify a file in the format of 'ase-sort.dat' used to translate "
    "indices in the Bader charge analysis file to the indices in the "
    "corresponding Atoms object.",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--bader-file",
    default="ACF.dat",
    help="Specify a path to the 'ACF.dat' file produced by the bader program.",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
    required=True,
)
@click.argument(
    "indices",
    nargs=-1,
    type=int,
)
def bader_sum(
    atoms: ase.Atoms,
    smart_mode: bool,
    sort_file: Path | None,
    bader_file: Path,
    indices: list[int],
) -> None:
    """Sum the bader charges of atoms specified by indices.

    INDICES is a list of integers indicating the indices for which to sum
    Bader charges. If --sort-file is set, the indices specified will still
    refer to the indices in the Atoms object before re-sorting. Note that
    if no indices are passed, then --smart-mode is activated and that if
    any indices are passed, then --smart-mode is ignored.

    Examples:
        ccu pop bader-sum --atoms final.traj --sort-file ase-sort.dat 0 1 2 22
        ccu pop bader-sum --atoms final.traj --smart-mode --sort-file ase-sort.dat
    """
    # Resort if sort_file supplied
    if sort_file:
        with Path(sort_file).open(mode="r", encoding="utf-8") as file:
            data: list[tuple[str, str]] = file.read().splitlines()
        resort = [int(x) for _, x in data]
        atoms = atoms[resort]

    # Attach charges
    ase.io.bader.attach_charges(atoms, bader_file)

    if indices:
        if smart_mode:
            logger.info(
                "Both INDICES and --smart-mode specified. Ignoring --smart-mode."
            )
        moiety_sum = sum(a.charge for a in atoms[indices])
        print(f"{indices!r}: {moiety_sum}")
    else:
        logger.debug("Smart mode activated")
        tag_to_indices = _get_tag_indices(atoms=atoms)
        for tag, tag_indices in tag_to_indices.items():
            moiety_sum = sum(a.charge for a in atoms[tag_indices])
            print(f"{tag}: {moiety_sum}")
