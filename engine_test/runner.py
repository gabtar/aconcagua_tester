"""Fastchess test runner - executes SPRT tests and parses results."""

import subprocess
import re
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .config import (
    FASTCHESS_BINARY,
    BOOK_DEFAULT,
    DEFAULT_TC,
    DEFAULT_ROUNDS,
    DEFAULT_CONCURRENCY,
    DEFAULT_SPRT_PARAMS,
    PGNS_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class TestResult:
    """Container for SPRT test results."""

    def __init__(self, test_id: str):
        self.id = test_id
        self.branch = ""
        self.branch_url = ""
        self.date = ""
        self.duration_seconds = 0
        self.sprt = {}
        self.tc = ""
        self.rounds = 0
        self.games_played = 0
        self.result = "running"
        self.elo_estimate = 0.0
        self.elo_lower = 0.0
        self.elo_upper = 0.0
        self.sprt_result = "continue"
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.pgn_saved = False
        self.label = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "branch": self.branch,
            "branch_url": self.branch_url,
            "date": self.date,
            "duration_seconds": self.duration_seconds,
            "sprt": self.sprt,
            "tc": self.tc,
            "rounds": self.rounds,
            "games_played": self.games_played,
            "result": self.result,
            "elo_estimate": self.elo_estimate,
            "elo_lower": self.elo_lower,
            "elo_upper": self.elo_upper,
            "sprt_result": self.sprt_result,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "pgn_saved": self.pgn_saved,
            "label": self.label,
        }


def parse_fastchess_output(output: str) -> Dict[str, Any]:
    """Parse fastchess output to extract game stats and SPRT results."""
    result = {
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "elo": 0.0,
        "elo_lower": 0.0,
        "elo_upper": 0.0,
        "sprt_result": "continue",
        "games": 0,
    }

    wins_match = re.search(r"W:\s*(\d+)", output)
    losses_match = re.search(r"L:\s*(\d+)", output)
    draws_match = re.search(r"D:\s*(\d+)", output)
    elo_match = re.search(r"ELO:\s*([-+]?\d+\.?\d*)\s*\(([-+]?\d+\.?\d*),\s*([-+]?\d+\.?\d*)\)", output)
    sprt_match = re.search(r"SPRT:\s*(accept|reject|continue)", output)
    games_match = re.search(r"Games:\s*(\d+)", output)

    if wins_match:
        result["wins"] = int(wins_match.group(1))
    if losses_match:
        result["losses"] = int(losses_match.group(1))
    if draws_match:
        result["draws"] = int(draws_match.group(1))
    if elo_match:
        result["elo"] = float(elo_match.group(1))
        result["elo_lower"] = float(elo_match.group(2))
        result["elo_upper"] = float(elo_match.group(3))
    if sprt_match:
        result["sprt_result"] = sprt_match.group(1)
    if games_match:
        result["games"] = int(games_match.group(1))

    return result


def run_sprt_test(
    dev_branch: str,
    tc: str = DEFAULT_TC,
    rounds: int = DEFAULT_ROUNDS,
    concurrency: int = DEFAULT_CONCURRENCY,
    sprt_elo0: float = DEFAULT_SPRT_PARAMS["elo0"],
    sprt_elo1: float = DEFAULT_SPRT_PARAMS["elo1"],
    alpha: float = DEFAULT_SPRT_PARAMS["alpha"],
    beta: float = DEFAULT_SPRT_PARAMS["beta"],
    book: str = BOOK_DEFAULT,
    save_pgn: bool = False,
    label: str = "",
    main_binary: Optional[str] = None,
    dev_binary: Optional[str] = None,
) -> TestResult:
    """Run an SPRT test between main and dev branch engines."""

    test_id = str(uuid.uuid4())[:8]
    test_result = TestResult(test_id)
    test_result.branch = dev_branch
    test_result.tc = tc
    test_result.rounds = rounds
    test_result.sprt = {
        "elo0": sprt_elo0,
        "elo1": sprt_elo1,
        "alpha": alpha,
        "beta": beta,
    }
    test_result.label = label
    test_result.pgn_saved = save_pgn

    from datetime import datetime
    from .builder import get_engine_path

    test_result.date = datetime.utcnow().isoformat() + "Z"

    if not main_binary:
        main_binary = str(get_engine_path("main"))
    if not dev_binary:
        dev_binary = str(get_engine_path(dev_branch))

    pgn_path = ""
    if save_pgn:
        pgn_dir = Path(PGNS_DIR) / test_id
        pgn_dir.mkdir(parents=True, exist_ok=True)
        pgn_path = str(pgn_dir / "games.pgn")

    cmd = [
        FASTCHESS_BINARY,
        "-engine", f"cmd={main_binary}", "name=main",
        "-engine", f"cmd={dev_binary}", "name=dev",
        "-each", f"tc={tc}",
        "-rounds", str(rounds),
        "-concurrency", str(concurrency),
        "-sprt", f"elo0={sprt_elo0}", f"elo1={sprt_elo1}",
        f"alpha={alpha}", f"beta={beta}",
        "-openings", f"file={book}", "format=epd", "order=random",
    ]

    if save_pgn and pgn_path:
        cmd.extend(["-pgnout", f"file={pgn_path}", "notation=uci"])

    logger.info(f"Running SPRT test: {dev_branch}")
    logger.info(f"Command: {' '.join(cmd)}")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        test_result.duration_seconds = int(time.time() - start_time)

        if result.returncode != 0:
            logger.error(f"Fastchess failed: {result.stderr}")
            test_result.result = "fail"
            return test_result

        parsed = parse_fastchess_output(result.stdout)
        test_result.wins = parsed["wins"]
        test_result.losses = parsed["losses"]
        test_result.draws = parsed["draws"]
        test_result.games_played = parsed["games"]
        test_result.elo_estimate = parsed["elo"]
        test_result.elo_lower = parsed["elo_lower"]
        test_result.elo_upper = parsed["elo_upper"]
        test_result.sprt_result = parsed["sprt_result"]

        if test_result.sprt_result == "accept":
            test_result.result = "pass"
        elif test_result.sprt_result == "reject":
            test_result.result = "fail"
        else:
            test_result.result = "continue"

        logger.info(f"Test completed: {test_result.result}")
        logger.info(f"Elo: {test_result.elo_estimate:.1f} ({test_result.elo_lower:.1f} - {test_result.elo_upper:.1f})")
        logger.info(f"SPRT: {test_result.sprt_result}")

    except Exception as e:
        test_result.result = "fail"
        test_result.duration_seconds = int(time.time() - start_time)
        logger.error(f"Test failed with exception: {e}")

    return test_result