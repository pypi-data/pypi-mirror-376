"""GUI utility functions.

Specifically, this module provides :func:`ccu.fancyplots._gui.utils.open_image`,
which opens a Tkinter-compatible version of an image shipped with
:mod:`ccu`, and :func:`ccu.fancyplots._gui.utils.print_easter_egg`, which prints
an Easter egg.
"""

import importlib

from PIL import Image
from PIL import ImageTk

from ccu.__about__ import __version__

_EASTER_EGG_WIDTH = 103


def open_image(name: str, width: int, height: int) -> ImageTk.PhotoImage:
    """Open Tkinter-compatible version of a ``ccu`` image.

    Args:
        name: The name of the image to open.
        width: The width of the image when opened.
        height: The height of the image when opened.

    Returns:
        A Tkinter-compatible version of the opened image.

    """
    images_ = importlib.resources.files("ccu.fancyplots.images")
    image = Image.open(images_.joinpath(name))
    resized_image = image.resize((width, height), Image.LANCZOS)
    tk_image = ImageTk.PhotoImage(resized_image)
    return tk_image


def print_easter_egg() -> None:
    """Print an Easter egg."""
    print("\n" * 3)
    print("#" * _EASTER_EGG_WIDTH)
    format_string = "{" + f":<{_EASTER_EGG_WIDTH - 2}}}"
    print("#" + format_string.format(" ") + "#")
    print("#" + format_string.format(" ") + "#")
    print(
        "#    *****    *****   ***    **   ****  **     **     ******   **       ***    **********  *******    #"
    )
    print(
        "#    **      **  **   **  *  **  *****   **  **       **   **  **      ** **   **********  **         #"
    )
    print(
        "#    ****   *** ***   **   ****  **        **         ** **    **     **   **      **      *******    #"
    )
    print(
        "#    **    **    **   **    ***  *****     **         **       ******  ** **       **           **    #"
    )
    print(
        "#    **   **     **   **     **   ****     **         **       ******   ***        **      *******    #"
    )
    print("#" + format_string.format(" ") + "#")
    print("#" + format_string.format(" ") + "#")
    print("#" + format_string.format(f"    Version: {__version__}") + "#")
    print(
        "#"
        + format_string.format("    Contact info: tiagojoaog@gmail.com")
        + "#"
    )
    print("#" + format_string.format(" ") + "#")
    print("#" * _EASTER_EGG_WIDTH)
    print("\n" * 3)
