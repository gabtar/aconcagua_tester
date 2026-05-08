# Aconcagua SPRT Test Tool - Specification

## 1. Directory Structure

```
/home/gabtar/git/engine_tester/
├── engine_test.py          # Main CLI tool (entry point)
├── requirements.txt         # Python dependencies
├── AGENTS.md               # This specification
├── fastchess/              # Fastchess binary
│   └── fastchess
├── books/                  # Opening books
│   └── UHO_Lichess_4852_v1.epd
├── results/                # Test results
│   ├── metadata/           # JSON test metadata
│   │   └── tests.json
│   └── pgns/              # PGN game files (optional)
│       └── {test_id}/
│           └── games.pgn
└── engines/                # Cloned branch sources (created at runtime)
    ├── main/               # Main branch source
    │   └── bin/aconcagua-linux-x86_64
    └── {branch_name}/     # Feature branch sources
        └── bin/aconcagua-linux-x86_64
```

## 2. CLI Interface

```bash
# Run a SPRT test
./engine_test.py run --dev <branch_name_or_url> [OPTIONS]
./engine_test.py run --dev feature/threats --rounds 2000 --sprt-elo0 0 --sprt-elo1 5
./engine_test.py run --dev feature/threats --tc "10+0.1" --save-pgn

# Show results (with colors)
./engine_test.py show                    # Show latest test
./engine_test.py show <branch_name>      # Show specific branch tests

# List all tests
./engine_test.py list

# Clean up
./engine_test.py clean engines   # Remove built binaries
./engine_test.py clean results    # Remove test history
./engine_test.py clean all       # Remove everything
```

### Run Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dev` | required | - | Branch name or git URL |
| `--rounds` | int | 1000 | Number of rounds |
| `--tc` | string | "8+0.08" | Time control (Cute-Chess format) |
| `--concurrency` | int | 3 | Concurrent games |
| `--sprt-elo0` | float | 0 | SPRT lower bound |
| `--sprt-elo1` | float | 5 | SPRT upper bound |
| `--alpha` | float | 0.05 | SPRT alpha |
| `--beta` | float | 0.05 | SPRT beta |
| `--book` | string | "books/UHO_Lichess_4852_v1.epd" | Opening book path |
| `--save-pgn` | flag | false | Save PGN files |
| `--label` | string | - | Custom label for test |

### Show Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `branch_name` | optional | latest | Branch to show results for |

## 3. Default Parameters

| Parameter | Default Value |
|-----------|---------------|
| Time control | `8+0.08` (8min + 0.08s increment) |
| Rounds | 1000 (STC) |
| Concurrency | 3 |
| SPRT elo0 | 0 |
| SPRT elo1 | 5 |
| Alpha/Beta | 0.05 / 0.05 |
| Opening book | `books/UHO_Lichess_4852_v1.epd` |

## 4. Result Storage Format

### Metadata (JSON)

Stored in `results/metadata/tests.json`:

```json
{
  "tests": [
    {
      "id": "uuid",
      "branch": "feature/threats",
      "branch_url": "https://github.com/gabtar/aconcagua/tree/feature/threats",
      "date": "2025-05-07T10:30:00Z",
      "duration_seconds": 3600,
      "sprt": {
        "elo0": 0,
        "elo1": 5,
        "alpha": 0.05,
        "beta": 0.05,
        "result": "accept|reject|continue"
      },
      "tc": "8+0.08",
      "rounds": 1000,
      "games_played": 1428,
      "result": "pass|fail|running",
      "elo_estimate": 2.3,
      "wins": 234,
      "losses": 198,
      "draws": 996,
      "pgn_saved": true,
      "label": "my-custom-label"
    }
  ]
}
```

### PGN Files

Stored in `results/pgns/{test_id}/games.pgn` when `--save-pgn` flag is used.

## 5. Key Features

1. **Auto-clone**: Clone branches from remote (`git@github.com:gabtar/aconcagua.git`) to `engines/` folder
2. **Auto-build**: Run `make build` to generate `bin/aconcagua-linux-x86_64`
3. **Cache builds**: Reuse existing binaries if branch source hasn't changed
4. **Parse fastchess output**: Extract SPRT result (accept/reject), Elo estimate, game stats
5. **Colored output**: Green for pass, red for fail with summary table
6. **Branch resolution**:
   - Local branch name (e.g., `feature/threats`)
   - Full URL (e.g., `https://github.com/gabtar/aconcagua/tree/feature/threats`)
   - Or just a descriptive name for testing local changes

## 6. Dependencies

### Python (requirements.txt)

- `chess` - Chess validation and move generation
- `pyyaml` - YAML parsing for config
- `colorama` - Terminal colors
- `tabulate` - Pretty tables

### System Requirements

- `git` - Clone repositories
- `make` - Build aconcagua
- `go` - Build aconcagua

## 7. Fastchess Integration

The tool wraps fastchess with the following command structure:

```
fastchess \
  -engine cmd={main_binary} name=main \
  -engine cmd={dev_binary} name=dev \
  -each tc={tc} \
  -rounds {rounds} \
  -concurrency {concurrency} \
  -sprt elo0={elo0} elo1={elo1} alpha={alpha} beta={beta} \
  -openings file={book} format=epd order=random \
  -pgnout file={pgn_path} notation=uci
```

## 8. Test Output Format (Colored)

```
=== Aconcagua SPRT Test Results ===

Branch: feature/threats
Date: 2025-05-07 10:30:00
SPRT: elo0=0, elo1=5 (alpha=0.05, beta=0.05)
TC: 8+0.08 | Rounds: 1000 | Games: 1428
Duration: 1h 2m 30s

┌─────────────────────────────────┐
│  RESULT: ✓ PASS                 │
│  Elo Estimate: +2.3 (0.8 - 3.8)  │
│  SPRT: ACCEPT                   │
└─────────────────────────────────┘

Wins: 234 (16.4%) | Draws: 996 (69.8%) | Losses: 198 (13.9%)
```

## 9. Error Handling

- If branch doesn't exist: show error with suggestion to check branch name
- If build fails: show Go error output, suggest checking branch for compilation errors
- If test interrupted: save partial results, allow resume with config file
- If fastchess crashes: log error, save partial game stats