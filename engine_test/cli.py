"""CLI - Command-line interface for the SPRT test tool."""

import click
import os

from . import __version__
from .config import (
    DEFAULT_TC,
    DEFAULT_ROUNDS,
    DEFAULT_CONCURRENCY,
    DEFAULT_SPRT_PARAMS,
    BOOK_DEFAULT,
    ENGINES_DIR,
    RESULTS_DIR,
)
from . import builder
from . import runner
from . import storage


@click.group()
@click.version_option(version=__version__)
def cli():
    """Aconcagua SPRT Test Tool - Run chess engine SPRT tests."""
    pass


@cli.command()
@click.option("--dev", required=True, help="Branch name or URL to test")
@click.option("--rounds", default=DEFAULT_ROUNDS, help="Number of rounds")
@click.option("--tc", default=DEFAULT_TC, help="Time control (Cute-Chess format)")
@click.option("--concurrency", default=DEFAULT_CONCURRENCY, help="Concurrent games")
@click.option("--sprt-elo0", default=DEFAULT_SPRT_PARAMS["elo0"], help="SPRT lower bound")
@click.option("--sprt-elo1", default=DEFAULT_SPRT_PARAMS["elo1"], help="SPRT upper bound")
@click.option("--alpha", default=DEFAULT_SPRT_PARAMS["alpha"], help="SPRT alpha")
@click.option("--beta", default=DEFAULT_SPRT_PARAMS["beta"], help="SPRT beta")
@click.option("--book", default=BOOK_DEFAULT, help="Opening book path")
@click.option("--save-pgn", is_flag=True, help="Save PGN game files")
@click.option("--label", default="", help="Custom label for this test")
def run(
    dev: str,
    rounds: int,
    tc: str,
    concurrency: int,
    sprt_elo0: float,
    sprt_elo1: float,
    alpha: float,
    beta: float,
    book: str,
    save_pgn: bool,
    label: str,
):
    """Run an SPRT test against the main branch."""

    if not os.path.exists(book):
        click.echo(f"Error: Opening book not found: {book}", err=True)
        return

    click.echo(f"Preparing to test branch: {dev}")

    click.echo("Building main branch engine...")
    try:
        builder.ensure_main_engine()
    except Exception as e:
        click.echo(f"Error building main engine: {e}", err=True)
        return

    click.echo(f"Building {dev} branch engine...")
    try:
        builder.build_engine(dev)
    except Exception as e:
        click.echo(f"Error building dev engine: {e}", err=True)
        return

    click.echo("Running SPRT test...")
    result = runner.run_sprt_test(
        dev_branch=dev,
        tc=tc,
        rounds=rounds,
        concurrency=concurrency,
        sprt_elo0=sprt_elo0,
        sprt_elo1=sprt_elo1,
        alpha=alpha,
        beta=beta,
        book=book,
        save_pgn=save_pgn,
        label=label,
    )

    storage.save_test(result)

    from .display import display_result
    display_result(result)


@cli.command()
@click.argument("branch", required=False)
def show(branch: str | None):
    """Show test results. Use 'latest' or branch name to filter."""
    if branch:
        tests = storage.get_tests_for_branch(branch)
    else:
        latest = storage.get_latest_test()
        if latest:
            tests = [latest]
        else:
            tests = []

    if not tests:
        click.echo("No test results found.")
        return

    from .display import display_test_list
    display_test_list(tests)


@cli.command()
def list():
    """List all test results."""
    tests = storage.load_tests()
    if not tests:
        click.echo("No test results found.")
        return

    from .display import display_test_list
    display_test_list(tests)


@cli.group()
def clean():
    """Clean up test data."""
    pass


@clean.command("engines")
@click.option("--branch", help="Specific branch to clean")
def clean_engines(branch: str | None):
    """Remove built engine binaries."""
    builder.cleanup_engines(branch)
    click.echo("Engine directories cleaned.")


@clean.command("results")
def clean_results():
    """Remove all test results."""
    storage.clear_results()
    click.echo("Test results cleared.")


@clean.command("all")
def clean_all():
    """Remove all engines and results."""
    builder.cleanup_engines()
    storage.clear_results()
    click.echo("All data cleaned.")


if __name__ == "__main__":
    cli()