"""Display - handles formatted output with colors for test results."""

import os
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

    main_branch = getattr(result, "main_branch", "main")
    click.echo(f"Test ID: {result.id}")
    click.echo(f"Branch: {result.branch} vs {main_branch}")
    click.echo(f"Date: {format_date_iso(result.date)}")
    click.echo(f"SPRT: elo0={result.sprt['elo0']}, elo1={
               result.sprt['elo1']} (alpha={result.sprt['alpha']}, beta={result.sprt['beta']})")
    click.echo(f"TC: {result.tc} | Rounds: {
               result.rounds} | Games: {result.games_played}")
    click.echo(f"Duration: {format_duration(result.duration_seconds)}")

    if result.label:
        click.echo(f"Label: {result.label}")

    click.echo("")

    if result.result == "pass":
        status = click.style("✓ PASS", fg="green", bold=True)
    elif result.result == "fail":
        status = click.style("✗ FAIL", fg="red", bold=True)
    else:
        status = click.style("○ PENDING", fg="yellow", bold=True)

    elo_str = f"+{result.elo_estimate:.1f}" if result.elo_estimate >= 0 else f"{
        result.elo_estimate:.1f}"
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

        click.echo(f"{wins_str} ({win_pct:.1f}%) | {draws_str} ({
                   draw_pct:.1f}%) | {losses_str} ({loss_pct:.1f}%)")


def display_test_details(test: Dict[str, Any]) -> None:
    """Display detailed information about a specific test by ID."""
    wins = test.get("wins", 0)
    losses = test.get("losses", 0)
    draws = test.get("draws", 0)

    if wins == 0 and losses == 0 and draws == 0 and test.get("result") == "pending":
        config_path = test.get("config_path", "")
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, "r") as f:
                config_data = json.load(f)
                stats = config_data.get("stats", {})
                for key, values in stats.items():
                    wins = values.get("wins", 0)
                    losses = values.get("losses", 0)
                    draws = values.get("draws", 0)
                    break

    click.echo("\n=== Test Details ===\n")

    click.echo(f"Test ID:     {test.get('id', 'N/A')}")
    click.echo(f"Branch:      {test.get('branch', 'N/A')
                               } vs {test.get('main_branch', 'main')}")
    click.echo(f"Date:        {format_date_iso(test.get('date', ''))}")
    click.echo(f"Label:       {test.get('label', 'N/A') or '(none)'}")

    click.echo("\n--- SPRT Parameters ---")
    sprt = test.get("sprt", {})
    click.echo(f"elo0:        {sprt.get('elo0', 0)}")
    click.echo(f"elo1:        {sprt.get('elo1', 0)}")
    click.echo(f"alpha:       {sprt.get('alpha', 0)}")
    click.echo(f"beta:        {sprt.get('beta', 0)}")

    click.echo("\n--- Game Statistics ---")
    tc = test.get("tc", "N/A")
    rounds = test.get("rounds", 0)
    games = test.get("games_played", 0)
    click.echo(f"Time Control: {tc}")
    click.echo(f"Total Rounds: {rounds}")
    click.echo(f"Games Played: {games}")
    duration = test.get("duration_seconds", 0)
    click.echo(f"Duration:    {format_duration(duration)}")

    total = wins + losses + draws
    if total > 0:
        click.echo(f"\n--- WDL ---")
        click.echo(f"Wins:        {wins} ({wins/total*100:.1f}%)")
        click.echo(f"Draws:       {draws} ({draws/total*100:.1f}%)")
        click.echo(f"Losses:      {losses} ({losses/total*100:.1f}%)")

    click.echo("\n--- Elo Analysis ---")
    elo = test.get("elo_estimate", 0)
    elo_lower = test.get("elo_lower", 0)
    elo_upper = test.get("elo_upper", 0)
    elo_str = f"+{elo:.1f}" if elo >= 0 else f"{elo:.1f}"
    click.echo(f"Elo:         {elo_str} ({elo_lower:.1f} - {elo_upper:.1f})")
    llr = test.get("llr", 0)
    click.echo(f"LLR:         {llr:.2f}")

    click.echo("\n--- SPRT Result ---")
    sprt_result = test.get("sprt_result", "continue")
    if sprt_result == "accept":
        result_str = click.style("ACCEPT", fg="green", bold=True)
    elif sprt_result == "reject":
        result_str = click.style("REJECT", fg="red", bold=True)
    else:
        result_str = click.style("PENDING", fg="yellow", bold=True)
    click.echo(f"Status:      {result_str}")

    click.echo("\n--- Files ---")
    pgn_saved = test.get("pgn_saved", False)
    click.echo(f"PGN Saved:   {'Yes' if pgn_saved else 'No'}")
    if pgn_saved:
        test_id = test.get("id", "")
        click.echo(f"PGN Path:    results/pgns/{test_id}/games.pgn")

    config_path = test.get("config_path", "")
    if config_path:
        click.echo(f"Config:      {config_path}")
        click.echo("\nTip: Use './engine_test.py resume' to continue this test")


def format_date_iso(iso_date: str) -> str:
    """Format ISO date string to yyyy-mm-dd hh:mm."""
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_date[:16]


def display_test_list(tests: List[Dict[str, Any]]) -> None:
    """Display a list of test results in a table."""

    if not tests:
        click.echo("No tests found.")
        return

    click.echo(f"{'ID':<10} {'Branch':<22} {'vs':<6} {'Date':<16} {
               'Result':<10} {'Elo':<10} {'SPRT':<10}")
    click.echo("-" * 95)

    for test in tests:
        test_id = test.get("id", "")[:8]
        main_branch = test.get("main_branch", "main")[:8]
        branch = test.get("branch", "")[:22]
        date = format_date_iso(test.get("date", ""))
        result = test.get("result", "")
        elo = test.get("elo_estimate", 0)
        sprt = test.get("sprt_result", "")

        if result == "pass":
            result_str = click.style("PASS", fg="green")
        elif result == "fail":
            result_str = click.style("FAIL", fg="red")
        else:
            result_str = click.style("PENDING", fg="yellow")

        elo_str = f"+{elo:.1f}" if elo >= 0 else f"{elo:.1f}"

        if sprt == "accept":
            sprt_str = click.style("ACCEPT", fg="green")
        elif sprt == "reject":
            sprt_str = click.style("REJECT", fg="red")
        else:
            sprt_str = click.style("PENDING", fg="yellow")

        click.echo(f"{test_id:<10} {branch:<22} {main_branch:<6} {
                   date:<16} {result_str:<10} {elo_str:<10} {sprt_str:<10}")
