"""Utilities for initializing ccu."""

import os
from pathlib import Path
import subprocess

import click

from ccu.settings import CCU_HOME

_PROFILE_LINES = "\n# Added by {0}\n. {1}\n"


def _write_completion_script(package: str, shell: str) -> Path:
    """Write the completion script."""
    hyphenated_package = f"{package.replace('_', '-')}"
    script = CCU_HOME.joinpath(f".{hyphenated_package}-complete.{shell}")
    env = {**os.environ}
    env[f"_{package.upper()}_COMPLETE"] = f"{shell}_source"

    if not script.exists() or (
        input("Completion script exists! Overwrite (Y/N)? ").lower() == "y"
    ):
        with script.open(mode="w", encoding="utf-8") as file:
            _ = subprocess.run(
                args=hyphenated_package,
                stdout=file,
                check=False,
                env=env,
            )
        click.echo(
            f"Completion script written to {script.relative_to(Path.home())}"
        )
    return script


@click.command(
    "init", context_settings={"help_option_names": ["-h", "--help"]}
)
def main() -> None:
    """Enable tab completion and create the ccu home directory."""
    # Create ccu home
    CCU_HOME.mkdir(parents=True, exist_ok=True)

    # Create .config/ccu/config.toml (shell_completion.sh)
    package = str(__package__).split(".")[0]
    shell = os.getenv("SHELL", "/bin/bash").split("/")[-1]
    script = _write_completion_script(package, shell)

    profile = Path.home().joinpath(f".{shell}rc")
    new_lines = _PROFILE_LINES.format(package, script)

    with profile.open(mode="r", encoding="utf-8") as file:
        lines = file.readlines()

    source_line = new_lines.splitlines()[-1]
    completion_added = any(line.rstrip() == source_line for line in lines)

    if not completion_added:
        with profile.open(mode="a", encoding="utf-8") as file:
            file.writelines(new_lines)

        click.echo(
            f"The following lines have been added to your .{shell}rc file"
        )
        click.echo(new_lines)
