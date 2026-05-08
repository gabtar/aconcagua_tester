# Aconcagua SPRT Test Tool

A command-line tool for running SPRT (Sequential Probability Ratio Test) tests on the Aconcagua chess engine. Compare development branches against the main branch to validate improvements before merging.

## Features

- **Auto-build**: Clones and builds engine branches automatically
- **SPRT Testing**: Statistical validation of engine strength changes
- **Result Tracking**: Stores test history with metadata (JSON)
- **Optional PGN**: Save game files for later analysis
- **Colored Output**: Clear visual indication of test results

## Requirements

- Python 3.10+
- Go (for building Aconcagua)
- Git

## Installation

```bash
cd aconcagua_tester
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

```bash
# Run a test with default parameters (1000 rounds, 8+0.08 TC, SPRT elo0=0 elo1=5)
./engine_test.py run --dev feature/your-branch

# Show latest test results
./engine_test.py show

# List all tests
./engine_test.py list
```

## Commands

### run

Run an SPRT test comparing a development branch against main.

```bash
./engine_test.py run --dev <branch> [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--dev` | (required) | Branch name or URL to test |
| `--rounds` | 1000 | Number of rounds |
| `--tc` | 8+0.08 | Time control (Cute-Chess format) |
| `--concurrency` | 3 | Concurrent games |
| `--sprt-elo0` | 0 | SPRT lower Elo bound |
| `--sprt-elo1` | 5 | SPRT upper Elo bound |
| `--alpha` | 0.05 | SPRT alpha (type I error) |
| `--beta` | 0.05 | SPRT beta (type II error) |
| `--book` | books/UHO_Lichess_4852_v1.epd | Opening book path |
| `--save-pgn` | false | Save PGN game files |
| `--label` | "" | Custom label for test |

**Examples:**

```bash
# Basic test
./engine_test.py run --dev feature/threats

# Custom time control and more rounds
./engine_test.py run --dev feature/threats --tc "10+0.1" --rounds 2000

# Save PGN files for analysis
./engine_test.py run --dev feature/threats --save-pgn

# Custom SPRT bounds
./engine_test.py run --dev feature/threats --sprt-elo0 -2.5 --sprt-elo1 2.5
```

### show

Show test results for a specific branch or the latest test.

```bash
./engine_test.py show [branch]
```

**Examples:**

```bash
# Show latest test
./engine_test.py show

# Show tests for specific branch
./engine_test.py show feature/threats
```

### list

List all test results.

```bash
./engine_test.py list
```

### clean

Clean up built engines and test results.

```bash
./engine_test.py clean <target>
```

**Targets:**

- `engines` - Remove built engine binaries
- `results` - Remove all test results
- `all` - Remove everything

**Examples:**

```bash
# Clean all engines
./engine_test.py clean engines

# Clean all results
./engine_test.py clean results

# Clean everything
./engine_test.py clean all
```

## Time Control Formats

The time control (`--tc`) uses Cute-Chess format:

- `8+0.08` - 8 minutes + 0.08 seconds increment
- `60+1` - 60 minutes + 1 second increment
- `10` - 10 seconds fixed time per move

## Output

The tool displays results with color-coded status:

- **Green** - Test passed (SPRT accepted)
- **Red** - Test failed (SPRT rejected)
- **Yellow** - Test ongoing (SPRT continue)

Example output:

```
=== Aconcagua SPRT Test Results ===

Branch: feature/threats
Date: 2026-05-07T10:30:00Z
SPRT: elo0=0, elo1=5 (alpha=0.05, beta=0.05)
TC: 8+0.08 | Rounds: 1000 | Games: 2000
Duration: 45m 30s

┌───────────────────────────────────┐
│  RESULT: ✓ PASS                   │
│  Elo Estimate: +2.3 (0.8 - 3.8)   │
│  SPRT: ACCEPT                     │
└───────────────────────────────────┘

Wins: 342 (17.1%) | Draws: 1316 (65.8%) | Losses: 342 (17.1%)
```

## Results Storage

Test results are stored in:

- **Metadata**: `results/metadata/tests.json`
- **PGN files**: `results/pgns/{test_id}/games.pgn` (if `--save-pgn` is used)

The metadata JSON includes:

- Test ID, branch, date
- SPRT parameters and results
- Game statistics (wins/losses/draws)
- Elo estimate with confidence interval

## Project Structure

```
aconcagua_tester/
├── engine_test.py          # Main CLI entry point
├── engine_test/            # Python package
│   ├── cli.py             # Click CLI commands
│   ├── config.py          # Configuration
│   ├── builder.py         # Git clone + build
│   ├── runner.py          # Fastchess execution
│   ├── storage.py         # Results persistence
│   └── display.py         # Colored output
├── fastchess/             # Fastchess binary
├── books/                 # Opening books
│   └── UHO_Lichess_4852_v1.epd
├── engines/               # Cloned branch sources (built at runtime)
├── results/               # Test results
│   ├── metadata/
│   └── pgns/
└── .venv/                 # Python virtual environment
```

## License

MIT