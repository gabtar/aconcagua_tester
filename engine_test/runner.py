"""Fastchess test runner - executes SPRT tests and parses results."""

import os
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


def _save_config_for_resume(test_id: str) -> str:
    """Save config.json for resuming a test later."""
    import os
    from .config import METADATA_DIR

    config_source = os.path.join(os.getcwd(), "config.json")
    if not os.path.exists(config_source):
        return ""

    os.makedirs(METADATA_DIR, exist_ok=True)
    config_dest = os.path.join(METADATA_DIR, f"{test_id}_config.json")

    import shutil
    shutil.copy2(config_source, config_dest)
    logger.info(f"Saved config for resume: {config_dest}")
    return config_dest


class TestResult:
    """Container for SPRT test results."""

    def __init__(self, test_id: str):
        self.id = test_id
        self.main_branch = "main"
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
        self.config_path = ""
        self.llr = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "main_branch": self.main_branch,
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
            "config_path": self.config_path,
            "llr": self.llr,
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
        "llr": 0.0,
    }

    wins_match = re.search(r"Wins:\s*(\d+)", output)
    losses_match = re.search(r"Losses:\s*(\d+)", output)
    draws_match = re.search(r"Draws:\s*(\d+)", output)
    elo_match = re.search(r"Elo:\s*([-+]?\d+\.?\d*)\s*\+/-\s*([-+]?\d+\.?\d*)", output)
    sprt_accept_match = re.search(r"H1 was accepted", output)
    sprt_reject_match = re.search(r"H1 was rejected", output)
    games_match = re.search(r"Games:\s*(\d+)", output)
    llr_match = re.search(r"LLR:\s*([-+]?\d+\.?\d*)", output)

    if wins_match:
        result["wins"] = int(wins_match.group(1))
    if losses_match:
        result["losses"] = int(losses_match.group(1))
    if draws_match:
        result["draws"] = int(draws_match.group(1))
    if elo_match:
        result["elo"] = float(elo_match.group(1))
        result["elo_lower"] = float(elo_match.group(2))
        result["elo_upper"] = float(elo_match.group(2))
    if sprt_accept_match:
        result["sprt_result"] = "accept"
    elif sprt_reject_match:
        result["sprt_result"] = "reject"
    if games_match:
        result["games"] = int(games_match.group(1))
    if llr_match:
        result["llr"] = float(llr_match.group(1))

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
    verbose: bool = False,
) -> TestResult:
    """Run an SPRT test between main and dev branch engines."""

    test_id = str(uuid.uuid4())[:8]
    test_result = TestResult(test_id)
    test_result.main_branch = "main"
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
        "-engine", f"cmd={dev_binary}", "name=dev",
        "-engine", f"cmd={main_binary}", "name=main",
        "-each", f"tc={tc}",
        "-rounds", str(rounds),
        "-repeat",
        "-concurrency", str(concurrency),
        "-recover",
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

        if verbose and result.stdout:
            print(result.stdout)

        test_result.duration_seconds = int(time.time() - start_time)

        config_path_local = os.path.join(os.getcwd(), "config.json")
        config_has_results = False
        if os.path.exists(config_path_local):
            with open(config_path_local, "r") as f:
                config_data = json.load(f)
                stats = config_data.get("stats", {})
                for key, values in stats.items():
                    test_result.wins = values.get("wins", 0)
                    test_result.losses = values.get("losses", 0)
                    test_result.draws = values.get("draws", 0)
                    test_result.games_played = test_result.wins + test_result.losses + test_result.draws
                    break

                sprt_data = config_data.get("sprt", {})
                test_result.llr = sprt_data.get("llr", 0.0)
                test_result.elo_estimate = sprt_data.get("elo", 0.0)

                if test_result.llr > sprt_elo1:
                    test_result.sprt_result = "accept"
                elif test_result.llr < sprt_elo0:
                    test_result.sprt_result = "reject"
                else:
                    test_result.sprt_result = "continue"

                config_has_results = test_result.games_played > 0

        if result.returncode != 0:
            logger.error(f"Fastchess failed with return code {result.returncode}")
            test_result.result = "fail"
            return test_result

        if verbose and result.stdout:
            print(result.stdout)

        output_to_parse = result.stdout if result.stdout else (result.stderr or "")

        if output_to_parse:
            parsed = parse_fastchess_output(output_to_parse)
            if parsed["games"] > 0:
                test_result.games_played = parsed["games"]
                test_result.elo_estimate = parsed["elo"]
                test_result.elo_lower = parsed["elo_lower"]
                test_result.elo_upper = parsed["elo_upper"]
                test_result.llr = parsed["llr"]
                config_has_results = True
            if parsed["sprt_result"] != "continue":
                test_result.sprt_result = parsed["sprt_result"]
        elif config_has_results:
            pass

        if test_result.sprt_result == "accept":
            test_result.result = "pass"
        elif test_result.sprt_result == "reject":
            test_result.result = "fail"
        else:
            test_result.result = "pending"
            config_path = _save_config_for_resume(test_id)
            if config_path:
                test_result.config_path = config_path

        logger.info(f"Test completed: {test_result.result}")
        logger.info(f"WDL: {test_result.wins}-{test_result.draws}-{test_result.losses} ({test_result.games_played} games)")
        logger.info(f"SPRT: {test_result.sprt_result}, LLR: {test_result.llr:.2f}")

    except Exception as e:
        test_result.result = "fail"
        test_result.duration_seconds = int(time.time() - start_time)
        logger.error(f"Test failed with exception: {e}")

    return test_result


# TODO: Handle tests that complete all games but never cross SPRT bounds
# When LLR stays within (elo0, elo1) range after all rounds are played,
# we should mark this as "inconclusive" rather than "pending"


def resume_sprt_test(original_test_id: str, config_path: str) -> TestResult:
    """Resume a pending test using an existing config.json file."""
    import os

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = json.load(f)

    test_id = original_test_id
    test_result = TestResult(test_id)
    test_result.main_branch = "main"

    engines = config.get("engines", [])
    if len(engines) >= 2:
        main_cmd = engines[0].get("cmd", "")
        dev_cmd = engines[1].get("cmd", "")
        if "main" in main_cmd:
            test_result.branch = os.path.basename(os.path.dirname(dev_cmd))
        else:
            test_result.branch = os.path.basename(os.path.dirname(main_cmd))

    from datetime import datetime
    test_result.date = datetime.utcnow().isoformat() + "Z"

    tc_config = engines[0].get("limit", {}).get("tc", {}) if engines else {}
    tc_time = tc_config.get("time", 8000) / 1000
    tc_inc = tc_config.get("increment", 80) / 1000
    test_result.tc = f"{tc_time}+{tc_inc}"

    sprt_config = config.get("sprt", {})
    test_result.sprt = {
        "elo0": sprt_config.get("elo0", 0),
        "elo1": sprt_config.get("elo1", 5),
        "alpha": sprt_config.get("alpha", 0.05),
        "beta": sprt_config.get("beta", 0.05),
    }

    test_result.rounds = config.get("rounds", 0)

    cmd = [
        FASTCHESS_BINARY,
        "-resume",
    ]

    logger.info(f"Resuming SPRT test: {test_result.branch}")
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
            logger.error(f"Fastchess resume failed: {result.stderr}")
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
        test_result.llr = parsed["llr"]

        if test_result.sprt_result == "accept":
            test_result.result = "pass"
        elif test_result.sprt_result == "reject":
            test_result.result = "fail"
        else:
            test_result.result = "pending"
            new_config_path = _save_config_for_resume(test_id)
            if new_config_path:
                test_result.config_path = new_config_path

        logger.info(f"Test completed: {test_result.result}")
        logger.info(f"Elo: {test_result.elo_estimate:.1f} ({test_result.elo_lower:.1f} - {test_result.elo_upper:.1f})")
        logger.info(f"SPRT: {test_result.sprt_result}, LLR: {test_result.llr:.2f}")

    except Exception as e:
        test_result.result = "fail"
        test_result.duration_seconds = int(time.time() - start_time)
        logger.error(f"Resume failed with exception: {e}")

    return test_result
