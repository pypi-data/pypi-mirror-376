"""Command-line interface for AutoCleanEEG-View."""

import sys
from pathlib import Path

import click

from autocleaneeg_view.viewer import load_eeg_file, view_eeg


@click.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--view",
    is_flag=True,
    help="Launch the MNE-QT Browser to view the data.",
)
def main(file, view):
    """Load and visualize EEG files (.set, .edf, .bdf) using MNE-QT Browser.

    FILE is the path to the EEG file to process.
    """
    try:
        # Load the EEG file
        eeg = load_eeg_file(file)
        if view:
            # Launch the viewer when requested
            view_eeg(eeg)
        else:
            # Just print basic info about the loaded file
            click.echo(f"Loaded {file} successfully:")
            click.echo("Use --view to visualize the data.")

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
