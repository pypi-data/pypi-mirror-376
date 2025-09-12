from ase import Atoms
import pytest

from ccu.pop import bader


@pytest.fixture(name="indices")
def fixture_indices() -> dict[int, list[int]]:
    indices = {
        1: [0, 1, 2],
    }

    return indices


def test_should_get_tag_indices(indices: dict[int, list[int]]) -> None:
    total_atoms = sum(len(value) for value in indices.values())
    tags = [0] * total_atoms
    for tag, to_tag in indices.items():
        for i in to_tag:
            tags[i] = tag

    atoms = Atoms("C" * total_atoms, tags=tags)
    assert bader._get_tag_indices(atoms=atoms) == indices
