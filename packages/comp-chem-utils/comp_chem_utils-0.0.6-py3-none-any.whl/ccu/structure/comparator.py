"""This module defines the Comparator class.

The Comparator class can be used to determine teh similarity of two structures
as follows:

>>> import ase
>>> from ccu.structure.comparator import Comparator
>>> co1 = ase.Atoms("CO", positions=[[0, 0, 0], [1, 0, 0]])
>>> co2 = ase.Atoms("CO", positions=[[0, 1, 1], [1, 1, 1]])
>>> oc = ase.Atoms("OC", positions=[[0, 0, 0], [1, 0, 0]])
>>> Comparator.check_similarity(co1, co2)
True
>>> Comparator.check_similarity(co1, oc)
False
"""

from collections.abc import Iterable
from collections.abc import Sequence
from copy import deepcopy
from itertools import permutations
import math
from typing import TYPE_CHECKING

import ase
import numpy as np
from numpy.linalg import norm

from ccu.structure import fingerprint

if TYPE_CHECKING:
    from numpy.typing import NDArray


class Comparator:
    """An object which compares the similarity of two structures."""

    @staticmethod
    def check_similarity(
        structure1: ase.Atoms, structure2: ase.Atoms, tol: float = 5e-2
    ) -> bool:
        """Determines similarity of two structures within a given tolerance.

        Args:
            structure1: An :class:`~ase.Atoms` instance representing the
                first structure to compare.
            structure2: An :class:`~ase.Atoms` instance representing the
                second structure to compare.
            tol: A float specifying the tolerance for the average cumulative
                displacement for fingerprint in Angstroms. Defaults to 5e-2.
                The average cumulative displacement is the cumulative
                displacement between each set of
                :class:`Fingerprints <ccu.structure.fingerprint.Fingerprint`
                derived `structure1` and `structure2` divided by the
                number of atoms represented in the
                :class:`~ccu.structure.fingerprint.Fingerprint`.

        Returns:
            A bool indicating whether or not the two structures are similar
            within the specified tolerance.

        Note:
            The notion of similarity here can be summarized as:

                Two structures are similar if they can be superimposed via a
                translation operation.

        .. seealso:: :meth:`.Comparator.calculate_cumulative_displacement`
        """
        if len(structure1) != len(structure2):
            return False

        fingerprints1 = fingerprint.Fingerprint.from_structure(structure1)
        fingerprints2 = fingerprint.Fingerprint.from_structure(structure2)
        fingerprints2 = list(
            Comparator.cosort_fingerprints(fingerprints1, fingerprints2)
        )
        for i, fingerprint_ in enumerate(fingerprints2):
            disp = Comparator.calculate_cumulative_displacement(
                fingerprints1[i], fingerprint_
            )
            if disp / len(fingerprints1[i]) > tol:
                return False

        return True

    @staticmethod
    def cosort_histograms(
        fingerprint1: fingerprint.Fingerprint,
        fingerprint2: fingerprint.Fingerprint,
    ) -> dict[str, np.ndarray]:
        """Minimizes the cumulative displacement of atoms in each fingerprint.

        Given the first fingerprint, this method determines the ordering of
        the second fingerprint's histogram which minimizes the cumulative
        displacement of atoms in each structure.

        The two supplied `Fingerprints` need not have the same keys or the
        same number of entries under each key. Such cases are handled as
        follows:

        Let :math:`k` be a key in both the histograms of `fingerprint1` and
        `fingerprint2`. Let :math:`p` be the iterable corresponding to the
        key :math:`k` in the histogram of `fingerprint1`, and let :math:`q`
        be the iterable corresponding to the key :math:`k` in the histogram of
        `fingerprint2`.

        If :math:`len(p) > len(q)`, then :math:`q` is ordered according to its
        match with the first :math:`len(q)` elements of :math:`p`.

        If :math:`len(p) <= len(q)`, then :math:`q` is ordered according to
        the best match with :math:`p` and the first :math:`len(p)` elements of
        :math:`q`.

        Args:
            fingerprint1: The :class:`ccu.structure.fingerprint.Fingerprint`
                object to be used as a reference for each displacement in the
                other `Fingerprint` object's histogram.
            fingerprint2: The :class:`ccu.structure.fingerprint.Fingerprint`
                object for which the optimally ordered histogram is to be
                determined.

        Returns:
            A dict constructed from `fingerprint2._histogram` mapping
            chemical symbols to a :class:`numpy.ndarray` containing the
            displacement vectors to atoms with the corresponding chemical
            symbol. The order of the displacement vectors is such that the
            cumulative displacement of the displacement vectors is minimized
            relative to `fingerprint1._histogram`.

        """
        histogram = {}
        for element, histogram2 in fingerprint2.items():
            minimal_cumulative_displacement = math.inf
            minimally_displaced_ordering = list(histogram2)
            if element not in fingerprint1:
                continue

            # This is used as the "reference" histogram from which the
            # displacement is to be minimized
            histogram1 = fingerprint1[element]
            perm_length = min(len(histogram1), len(histogram2))
            displacements_permutations = permutations(
                histogram2, r=perm_length
            )
            for displacements in displacements_permutations:
                cumulative_displacement = 0.0
                for i, displacement in enumerate(displacements):
                    cumulative_displacement += float(
                        norm(histogram1[i] - displacement)
                    )

                if cumulative_displacement < minimal_cumulative_displacement:
                    minimal_cumulative_displacement = cumulative_displacement
                    minimally_displaced_ordering = list(displacements)

            missing_displacements = Comparator._missing_displacements(
                histogram2, minimally_displaced_ordering
            )
            minimally_displaced_ordering.extend(missing_displacements)
            histogram[element] = np.vstack(minimally_displaced_ordering)

        return histogram

    @staticmethod
    def _missing_displacements(
        all_displacements: "Iterable[NDArray]",
        minimally_displaced_ordering: "Iterable[NDArray]",
    ) -> "list[NDArray]":
        """Determines the displacements not in the M.D.O.

        Args:
            all_displacements: All displacements.
            minimally_displaced_ordering: The displacements in the minimally
                displaced ordering (M.D.O.)

        Returns:
            The missing displacements.
        """
        missing_displacements = []
        for displacement in all_displacements:
            for included_displacement in minimally_displaced_ordering:
                displacement_missing = True
                if (displacement == included_displacement).all():
                    displacement_missing = False
                    break

            if displacement_missing:
                missing_displacements.append(displacement)

        return missing_displacements

    @staticmethod
    def cosort_fingerprints(
        fingerprints1: Sequence[fingerprint.Fingerprint],
        fingerprints2: Sequence[fingerprint.Fingerprint],
    ) -> tuple[fingerprint.Fingerprint, ...]:
        """Determines the second fingerprints's minimally displaced ordering.

        The minimally displaced ordering of the second
        :class:`~ccu.structure.fingerprint.Fingerprint` list
        relative to the first is the ordering of the second supplied iterable
        of :class:`Fingerprints <ccu.structure.fingerprint.Fingerprint>` which
        minimizes the cumulative displacement across
        the two iterables of
        :class:`Fingerprints <ccu.structure.fingerprint.Fingerprint>`.

        Args:
            fingerprints1: An iterable containing
                :class:`~ccu.structure.fingerprint.Fingerprint` instances.
            fingerprints2: An iterable containing
                :class:`~ccu.structure.fingerprint.Fingerprint` instances.

            Note that the two iterables must be of the same length and that the
            :meth:`ccu.structure.fingerprint.Fingerprint.values` methods of all
            :class:`~ccu.structure.fingerprint.Fingerprint` instances across the
            two iterables must be of the same length.

        Returns:
            A tuple containing the ordering of `fingerprints2` which
            minimizes the cumulative displacement across the two iterables of
            :class:`Fingerprints <ccu.structure.fingerprint.Fingerprint>`.

        Raises:
            RuntimeError: Unable to find minimally displaced fingerprint.
        """
        minimal_cumulative_displacement = math.inf
        fingerprints_permutations = list(
            permutations(fingerprints2, r=len(fingerprints2))
        )
        mimimally_displaced_fingerprints = None
        for fingerprints in fingerprints_permutations:
            cumulative_displacement = 0.0
            for i, fingerprint_ in enumerate(fingerprints):
                fingerprint_.update(
                    Comparator.cosort_histograms(
                        fingerprints1[i], fingerprint_
                    )
                )
                displacement = Comparator.calculate_cumulative_displacement(
                    fingerprints1[i], fingerprint_
                )
                cumulative_displacement += displacement

            if cumulative_displacement < minimal_cumulative_displacement:
                minimal_cumulative_displacement = cumulative_displacement
                mimimally_displaced_fingerprints = deepcopy(fingerprints)

        if mimimally_displaced_fingerprints is None:
            msg = "Something went wrong!"
            raise RuntimeError(msg)
        return mimimally_displaced_fingerprints

    @staticmethod
    def calculate_cumulative_displacement(
        fingerprint1: fingerprint.Fingerprint,
        fingerprint2: fingerprint.Fingerprint,
    ) -> float:
        """Calculates the cumulative displacement for `fingerprint2`.

        The cumulative displacement is calculated for
        `fingerprint2` relative to the corresponding atomic positions in
        `fingerprint1`.

        The cumulative displacement is defined as follows:

        Note that each row in each :class:`numpy.ndarray` associated with each
        histogram key corresponds to a displacement vector between two atoms.
        With each such displacement vector in the histogram of
        `fingerprint1`, we can identify a corresponding displacement vector
        in the histogram of `fingerprint2` as the displacement vector
        associated with the same histogram key and index. We then define a
        difference vector as the difference between a displacement vector in
        `fingerprint1` and its counterpart in `fingerprint2`. The set of
        all difference vectors is defined on the basis  of `fingerprint1`.
        That is, if :math:`X` is the set of all displacement vectors in
        `fingerprint1` and :math:`Y` is the set of all corresponding vectors
        in `fingerprint2`, the set of all difference vectors is the set of
        all vectors :math:`x - y` where :math:`x` is a displacement
        vector in fingerprint1 and y is the corresponding displacement vector
        in :math:`Y`. (Note that this requires that the histogram of
        `fingerprint2` must include all the keys that the histogram
        of `fingerprint1` includes. Additionally, this requires that for
        each key in the histogram of `fingerprint1`, the value in
        `fingerprint2` includes at least as many displacement vectors as the
        value in `fingerprint1`.) The cumulative displacement is then
        defined as the sum of the norms of all the difference vectors
        corresponding to `fingerprint1` and `fingerprint2`.

        Args:
            fingerprint1: The :class:`.fingerprint.Fingerprint` instance used
                as a reference to calculate the cumulative displacement.
            fingerprint2: The second :class:`.fingerprint.Fingerprint`
                instance used to calculate the cumulative displacement.

        Returns:
            A float representing the cumulative displacement for
            `fingerprint2` relative to `fingerprint1`.

        """
        cumulative_displacement = 0.0
        for element in fingerprint1:
            for i, displacement in enumerate(fingerprint1[element]):
                d = norm(displacement - fingerprint2[element][i])
                cumulative_displacement += float(d)

        return cumulative_displacement
