"""Command-line interface for FancyPlots."""

from pathlib import Path
import tkinter as tk

import click

from ccu.fancyplots._gui.root import FancyPlotsGUI


@click.command(
    name="fed",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--cache",
    "cache_file",
    type=click.Path(path_type=Path),
    help="Load fancyplots with a cached session.",
    metavar="CACHE_FILE",
)
@click.option(
    "--data",
    "data_file",
    type=click.Path(path_type=Path),
    help="Initialize fancyplots with free energy diagram data. "
    "This should point to the result of dumping an instance of "
    "FEDData to a json file.",
    metavar="DATA_FILE",
)
@click.option(
    "--style",
    "style_file",
    type=click.Path(path_type=Path),
    help="Specify a style file.",
    metavar="STYLE_FILE",
)
def main(cache_file: Path, data_file: Path, style_file: Path) -> None:
    """Create free energy diagrams with the FancyPlots GUI."""
    root = tk.Tk()
    app = FancyPlotsGUI(
        cache_file=cache_file,
        data_file=data_file,
        style_file=style_file,
        master=root,
    )
    app.master.mainloop()
