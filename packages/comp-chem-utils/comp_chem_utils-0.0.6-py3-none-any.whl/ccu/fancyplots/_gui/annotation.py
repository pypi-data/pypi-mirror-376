"""GUI elements for defining free energy diagram annotations.

This module defines the :class:`AnnotationSection` class.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ccu.fancyplots._gui.frames import FancyFormatFrame
from ccu.fancyplots._gui.frames import UpdatableFrame
from ccu.fancyplots.data import Annotation
from ccu.fancyplots.data import FEDData
from ccu.fancyplots.validation import validator_from_type

if TYPE_CHECKING:
    from ccu.fancyplots._gui.root import FancyPlotsGUI

logger = logging.getLogger(__name__)


class AnnotationSection(ttk.LabelFrame, UpdatableFrame):
    """GUI component for adding annotations to the free energy diagram.

    Attributes:
        annotations: A list of :class:`ccu.fancyplots.data.Annotation`

    """

    def __init__(self, parent: "FancyPlotsGUI", *args, **kwargs) -> None:
        """Create section for adding annotations to the free energy diagram."""
        super().__init__(
            parent._frame, *args, text="Add Annotations", **kwargs
        )
        self.parent = parent
        int_validator = validator_from_type(int)
        str_validator = validator_from_type(str)
        self._text_frame = FancyFormatFrame(
            self, label="Additional Text:", validator=str_validator
        )
        self._x_frame = FancyFormatFrame(
            self, label="X Coordinate:", validator=int_validator
        )
        self._y_frame = FancyFormatFrame(
            self, label="Y Coordinate:", validator=int_validator
        )
        self._color_frame = FancyFormatFrame(
            self, label="Color:", validator=str_validator
        )
        self._font_frame = FancyFormatFrame(
            self, label="Fontsize:", validator=int_validator
        )
        self._index_frame, self._annotation_var = self._create_spinbox_frame()
        self._save_button = self.create_save_button()
        self._auto_annotate_button = self.create_auto_annotate_button()
        self.annotations = [Annotation()]
        self._organize()

    def _create_spinbox_frame(self) -> tuple[ttk.LabelFrame, tk.IntVar]:
        frame = ttk.LabelFrame(self)
        var = tk.IntVar(self, 1)
        _ = ttk.Spinbox(
            frame,
            from_=1,
            to=100,
            state="readonly",
            textvariable=var,
            width=3,
            command=self.update_frames,
        ).pack(expand=True, fill="both", side="left")
        return frame, var

    def update_frames(self) -> None:
        """Update the values in the subframes with the annotation."""
        logger.debug(
            "Updating frames in %s.%s", __package__, self.__class__.__name__
        )
        index = self._annotation_var.get() - 1

        if len(self.annotations) <= index:
            self.annotations.append(Annotation())

        self._text_frame.value = self.annotations[index].text
        self._x_frame.value = self.annotations[index].x
        self._y_frame.value = self.annotations[index].y
        self._color_frame.value = self.annotations[index].color
        self._font_frame.value = self.annotations[index].fontsize
        logger.debug(f"Displaying annotation with index: {index}")

    def save_annotation(self) -> None:
        """Save the created annotation data."""
        logger.debug("Saving annotation")
        index = self._annotation_var.get() - 1
        self.annotations[index] = Annotation(
            color=self._color_frame.value,
            fontsize=float(self._font_frame.value),
            text=self._text_frame.value,
            x=float(self._x_frame.value),
            y=float(self._y_frame.value),
        )
        logger.debug(f"Saved annotation with index: {index}")

    def create_save_button(self) -> ttk.Button:
        """Create a save button."""
        return ttk.Button(
            self,
            text="Save Text",
            command=self.save_annotation,
        )

    def _organize(self) -> None:
        """Organize widgets into 1x7 grid."""
        self._text_frame.grid(row=1, column=1, rowspan=2, sticky=tk.NSEW)
        self._color_frame.grid(row=3, column=1, rowspan=2, sticky=tk.NSEW)
        self._font_frame.grid(row=1, column=2, rowspan=2, sticky=tk.NSEW)
        self._x_frame.grid(row=3, column=2, rowspan=2, sticky=tk.NSEW)
        self._y_frame.grid(
            row=1, column=3, rowspan=2, columnspan=2, sticky=tk.NSEW
        )
        self._index_frame.grid(row=3, column=3, rowspan=2, sticky=tk.NSEW)
        self._save_button.grid(row=3, column=4, sticky=tk.NSEW)
        self._auto_annotate_button.grid(row=4, column=4, sticky=tk.NSEW)

    def create_auto_annotate_button(self) -> ttk.Button:
        """Create a auto annotate button."""
        return ttk.Button(
            self,
            text="Auto-Annotate",
            command=self.auto_annotate,
        )

    def auto_annotate(self) -> None:
        """Automatically annotate FED with mechanism step names."""
        logger.debug("Auto-annotating free energy diagram")
        data = self.parent.sections["mechanism"].diagram_data  # type: ignore[has-type]
        annotations = auto_annotate(data)
        self.annotations.extend(annotations)
        self.update_frames()


def auto_annotate(data: FEDData) -> list[Annotation]:
    """Automatically generate annotations from free energy data.

    Note:
        Duplicate annotations are not added.
    """
    annotations: list[Annotation] = []

    for energies, pathway in zip(
        data["energy_data"], data["mechanism"], strict=True
    ):
        step_count = -1
        for energy, step in zip(energies, pathway, strict=True):
            step_count += 2

            if energy is None:
                continue

            step_is_ts = step.split("_")[0].upper() == "TS"
            x_value = step_count - 1.0 if step_is_ts else step_count - 0.5
            annotation = Annotation(text=step, x=x_value, y=energy)

            if annotation not in annotations:
                annotations.append(annotation)

    return annotations
