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
@click.option("--verbose", is_flag=True, help="Show fastchess output in real-time")
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
    verbose: bool,
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
        verbose=verbose,
    )

    storage.save_test(result)

    from .display import display_result
    display_result(result)


@cli.command()
@click.argument("identifier", required=False)
def show(identifier: str | None):
    """Show test results. Use test ID, branch name, or 'latest'."""
    if not identifier:
        latest = storage.get_latest_test()
        if latest:
            from .display import display_test_details
            display_test_details(latest)
        else:
            click.echo("No test results found.")
        return

    test = storage.get_test_by_id(identifier)
    if test:
        from .display import display_test_details
        display_test_details(test)
        return

    tests = storage.get_tests_for_branch(identifier)
    if tests:
        from .display import display_test_list
        display_test_list(tests)
        return

    click.echo(f"No test found for '{identifier}'. Use a test ID, branch name, or 'latest'.")


@cli.command()
def list():
    """List all test results."""
    tests = storage.load_tests()
    if not tests:
        click.echo("No test results found.")
        return

    from .display import display_test_list
    display_test_list(tests)


@cli.command()
@click.argument("test_id", required=False)
def resume(test_id: str | None):
    """Resume a pending test using the saved config.json."""
    if not test_id:
        pending = storage.get_pending_tests()
        if not pending:
            click.echo("No pending tests found.")
            return
        click.echo("Pending tests:")
        for p in pending:
            click.echo(f"  {p['id']} - {p['branch']} vs {p.get('main_branch', 'main')} ({p.get('games_played', 0)} games)")
        click.echo("\nUsage: ./engine_test.py resume <test_id>")
        return

    test = storage.get_test_by_id(test_id)
    if not test:
        click.echo(f"Test not found: {test_id}")
        return

    if test.get("result") != "pending":
        click.echo(f"Test {test.get('id')} is not pending (result: {test.get('result')})")
        return

    config_path = test.get("config_path", "")
    if not config_path or not os.path.exists(config_path):
        click.echo(f"Config file not found: {config_path}")
        return

    import shutil
    workdir_config = os.path.join(os.getcwd(), "config.json")
    shutil.copy2(config_path, workdir_config)
    click.echo(f"Copied config to {workdir_config}")

    branch = test.get("branch", "")
    main_branch = test.get("main_branch", "main")

    click.echo(f"Resuming test: {branch} vs {main_branch}")

    try:
        result = runner.resume_sprt_test(test.get("id"), workdir_config)
        storage.save_test(result)

        from .display import display_result
        display_result(result)
    except Exception as e:
        click.echo(f"Error resuming test: {e}", err=True)


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