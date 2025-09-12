"""Module that contains the command line app."""

import importlib
import logging
from pathlib import Path

import click

from ccu import SETTINGS
from ccu.__about__ import __version__
from ccu._cli._utils import configure_logging

COMMANDS = (
    ("ccu.adsorption._cli", "adsorb"),
    ("ccu.pop._cli", "pop"),
    ("ccu._cli._init", "init"),
    ("ccu.fancyplots._cli", "fed"),
    ("ccu.structure._cli", "structure"),
    ("ccu.thermo._cli", "thermo"),
)


@click.group(
    name="ccu",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    default=False,
    help="Show the version and exit.",
)
@click.option(
    "-v",
    "--verbose",
    "verbosity",
    default=0,
    count=True,
    help="Control how much information is printed to the terminal. This "
    "option can be repeated.",
)
@click.option(
    "-q",
    "--quiet",
    "quietness",
    default=0,
    count=True,
)
@click.option(
    "--log-file",
    default=None,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Specify a log file for all logging messages.",
)
@click.option(
    "--log-level",
    default="WARNING",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    help="Specify the log level for all logging messages.",
)
def main(
    version: bool, verbosity: int, quietness: int, log_file, log_level: str
) -> None:
    """
       \b
      ___ ___ _   _
     / __/ __| | | |
    | (_| (__| |_| |
     \\___\\___|\\__,_|
    """  # noqa: D205, D212, D301, D415
    if version:
        click.echo(__version__)

    console_log_level = 10 * (quietness - verbosity) + logging.WARNING
    file_log_level = getattr(logging, log_level.upper())
    SETTINGS.LOG_LEVEL = file_log_level
    SETTINGS.LOG_FILE = log_file

    configure_logging(console_log_level)


def add_subcommands() -> None:
    """Add the subcommands."""
    for module, name in COMMANDS:
        command = importlib.import_module(module).main
        main.add_command(command, name=name)


add_subcommands()
