"""Configuration defaults and parameters for SPRT tests."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_TC = "8+0.08"
DEFAULT_ROUNDS = 5000
DEFAULT_CONCURRENCY = 3

DEFAULT_SPRT_PARAMS = {
    "elo0": 0,
    "elo1": 5,
    "alpha": 0.05,
    "beta": 0.05,
}

ACONCAGUA_REPO = "git@github.com:gabtar/aconcagua.git"
ACONCAGUA_MAIN_BRANCH = "main"

BOOK_DEFAULT = os.path.join(BASE_DIR, "books", "UHO_Lichess_4852_v1.epd")
FASTCHESS_BINARY = os.path.join(BASE_DIR, "fastchess", "fastchess")
ENGINES_DIR = os.path.join(BASE_DIR, "engines")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
METADATA_DIR = os.path.join(RESULTS_DIR, "metadata")
PGNS_DIR = os.path.join(RESULTS_DIR, "pgns")
METADATA_FILE = os.path.join(METADATA_DIR, "tests.json")
