"""Setup the cli by creating the main Typer application (blockperf_app) and
adding the (sub)commands to it."""

import typer
from rich.console import Console

from blockperf.commands.analyze import analyze_app
from blockperf.commands.base import version_cmd
from blockperf.commands.monitor import monitor_app
from blockperf.commands.run import run_app

console = Console()


# Initialize the Typer application
blockperf_app = typer.Typer(
    name="blockperf",
    help="A CLI application for block performance analysis",
    add_completion=True,
    no_args_is_help=True,
)

# Add base commands directly to the app
blockperf_app.command("version")(version_cmd)
blockperf_app.add_typer(analyze_app)
blockperf_app.add_typer(monitor_app)
blockperf_app.add_typer(run_app)


def mycallback():
    """Creates a single user Hiro Hamada. In the next version it will create 5 more users."""
    console.print("Y A Y")
