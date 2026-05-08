"""Display - handles formatted output with colors for test results."""

import click
from typing import List, Dict, Any
from datetime import datetime


def format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def display_result(result) -> None:
    """Display a single test result with colors."""

    click.echo("\n=== Aconcagua SPRT Test Results ===\n")

    click.echo(f"Branch: {result.branch}")
    click.echo(f"Date: {result.date}")
    click.echo(f"SPRT: elo0={result.sprt['elo0']}, elo1={result.sprt['elo1']} (alpha={result.sprt['alpha']}, beta={result.sprt['beta']})")
    click.echo(f"TC: {result.tc} | Rounds: {result.rounds} | Games: {result.games_played}")
    click.echo(f"Duration: {format_duration(result.duration_seconds)}")

    if result.label:
        click.echo(f"Label: {result.label}")

    click.echo("")

    if result.result == "pass":
        status = click.style("✓ PASS", fg="green", bold=True)
    elif result.result == "fail":
        status = click.style("✗ FAIL", fg="red", bold=True)
    else:
        status = click.style("○ CONTINUE", fg="yellow", bold=True)

    elo_str = f"+{result.elo_estimate:.1f}" if result.elo_estimate >= 0 else f"{result.elo_estimate:.1f}"
    elo_range = f"({result.elo_lower:.1f} - {result.elo_upper:.1f})"

    sprt_str = result.sprt_result.upper()
    if result.sprt_result == "accept":
        sprt_str = click.style(sprt_str, fg="green")
    elif result.sprt_result == "reject":
        sprt_str = click.style(sprt_str, fg="red")
    else:
        sprt_str = click.style(sprt_str, fg="yellow")

    border = "─" * 35
    click.echo(f"┌{border}┐")
    click.echo(f"│  RESULT: {status:<24}│")
    click.echo(f"│  Elo Estimate: {elo_str:<14}{elo_range:<9}│")
    click.echo(f"│  SPRT: {sprt_str:<24}│")
    click.echo(f"└{border}┘")

    click.echo("")

    total = result.wins + result.losses + result.draws
    if total > 0:
        win_pct = (result.wins / total) * 100
        loss_pct = (result.losses / total) * 100
        draw_pct = (result.draws / total) * 100

        wins_str = click.style(f"Wins: {result.wins}", fg="green")
        draws_str = click.style(f"Draws: {result.draws}", fg="yellow")
        losses_str = click.style(f"Losses: {result.losses}", fg="red")

        click.echo(f"{wins_str} ({win_pct:.1f}%) | {draws_str} ({draw_pct:.1f}%) | {losses_str} ({loss_pct:.1f}%)")


def display_test_list(tests: List[Dict[str, Any]]) -> None:
    """Display a list of test results in a table."""

    if not tests:
        click.echo("No tests found.")
        return

    click.echo(f"{'Branch':<30} {'Date':<20} {'Result':<10} {'Elo':<12} {'SPRT':<10}")
    click.echo("-" * 90)

    for test in tests:
        branch = test.get("branch", "")[:28]
        date = test.get("date", "")[:19]
        result = test.get("result", "")
        elo = test.get("elo_estimate", 0)
        sprt = test.get("sprt_result", "")

        if result == "pass":
            result_str = click.style("PASS", fg="green")
        elif result == "fail":
            result_str = click.style("FAIL", fg="red")
        else:
            result_str = click.style("CONTINUE", fg="yellow")

        elo_str = f"+{elo:.1f}" if elo >= 0 else f"{elo:.1f}"

        if sprt == "accept":
            sprt_str = click.style("ACCEPT", fg="green")
        elif sprt == "reject":
            sprt_str = click.style("REJECT", fg="red")
        else:
            sprt_str = click.style("CONTINUE", fg="yellow")

        click.echo(f"{branch:<30} {date:<20} {result_str:<10} {elo_str:<12} {sprt_str:<10}")