"""CLI commands for population analysis."""

import logging

import click

from ccu.pop.bader import bader_sum

logger = logging.getLogger(__package__.split(".")[0])


@click.group(name=__package__.split(".")[-1])
def main():
    """Population analysis tools."""


main.add_command(bader_sum)
