# NESS Ammeter QA — Testing Framework

A Python-based testing framework for current measurement systems using multiple ammeter types (Greenlee, ENTES, CIRCUTOR). Built as part of a technical home assignment for NES.

---

## Project Structure

Test\_QA\_expanded/

├── main.py                           \# Starts all 3 ammeters and requests measurements

├── config/

│   └── config.yaml                   \# Sampling, ammeter, and analysis configuration

├── ammeters/                         \# PEP 8 compliant package (lowercase)

│   ├── base\_ammeter.py               \# Base TCP socket server for all ammeters

│   ├── greenlee\_ammeter.py           \# Ohm's Law emulator (port 5000\)

│   ├── entes\_ammeter.py              \# Hall Effect emulator (port 5001\)

│   ├── circutor\_ammeter.py           \# Rogowski Coil emulator (port 5002\)

│   └── client.py                     \# TCP client for measurement requests

├── src/

│   ├── testing/

│   │   ├── ammeter\_tester.py         \# Unified API: sample, statistics, save results, compare accuracy

│   │   └── test\_framework.py         \# Orchestrator: runs full test cycle from config

│   └── utils/

│       ├── config.py                 \# Loads config.yaml

│       ├── logger.py                 \# Writes logs to results/logs/

│       ├── visualizer.py             \# Generates charts from results (bonus)

│       └── Utils.py                  \# Utility functions

├── examples/

│   └── run\_tests.py                  \# Demo: runs all 3 ammeters, saves results, plots charts

├── tests/

│   ├── conftest.py                   \# Shared fixtures \+ session-scoped emulator startup

│   ├── run\_pipeline.sh               \# Test pipeline script with stage control

│   ├── test\_smoke.py                 \# Smoke tests (2 tests)

│   ├── test\_ammeter\_tester.py        \# Unit tests for AmmeterTester (19 tests)

│   ├── test\_ammeter\_framework.py     \# Unit tests for AmmeterTestFramework (4 tests)

│   ├── test\_functional.py            \# Functional tests (11 tests)

│   ├── test\_error\_simulation.py      \# Error simulation tests (13 tests)

│   └── test\_e2e.py                   \# End-to-end test (1 test)

├── results/                          \# Auto-generated JSON result files

│   ├── logs/                         \# Auto-generated log files

│   │   └── README.md                 \# Log files guide

│   └── plots/                        \# Auto-generated visualization charts

├── pytest.ini                        \# pytest configuration and markers

└── requirements.txt                  \# Python dependencies

---

## Installation

\# Navigate to the project directory

cd Test\_QA\_expanded

\# Create and activate virtual environment

python3 \-m venv venv

source venv/bin/activate  \# Mac/Linux

\# Install dependencies

pip install \-r requirements.txt

---

## Usage

### Run the demo (all 3 ammeters)

python3 \-m examples.run\_tests

Starts all 3 ammeter emulators, collects measurements, calculates statistics, saves results to `results/`, generates visualization charts, and prints accuracy comparison.

### Run a quick measurement check

python3 main.py

---

## Configuration

Edit `config/config.yaml` to control sampling behavior:

testing:

  sampling:

    measurements\_count: 4       \# Number of measurements per run

    total\_duration\_seconds: 10  \# Total test duration

    sampling\_frequency\_hz: 0.5  \# Measurements per second

---

## Testing

### Run the full pipeline (recommended)

./tests/run\_pipeline.sh

Runs all stages in order: smoke → unit → functional → e2e.

- **smoke** and **unit** stop the pipeline immediately on failure  
- **functional** and **e2e** continue on failure and show a full summary

### Run specific stages

./tests/run\_pipeline.sh smoke                  \# Smoke only

./tests/run\_pipeline.sh unit                   \# Unit only

./tests/run\_pipeline.sh functional             \# Functional only

./tests/run\_pipeline.sh e2e                    \# E2E only

./tests/run\_pipeline.sh smoke unit             \# Smoke then unit

./tests/run\_pipeline.sh functional e2e         \# Functional then e2e

### Run by marker

./venv/bin/python3 \-m pytest tests/ \-v \-m smoke        \# Sanity check only

./venv/bin/python3 \-m pytest tests/ \-v \-m unit         \# Unit tests only (no emulators)

./venv/bin/python3 \-m pytest tests/ \-v \-m functional   \# Functional tests

./venv/bin/python3 \-m pytest tests/ \-v \-m e2e          \# End-to-end test

**Note:** When running by marker, pytest collects all tests and filters by marker. `deselected` in the output indicates tests skipped due to marker filtering — this is expected behavior.

### Test coverage summary

| File | Type | Tests | Description |
| :---- | :---- | :---- | :---- |
| `test_smoke.py` | Smoke | 2 | System starts and responds |
| `test_ammeter_tester.py` | Unit | 19 | Validations, happy path, edge cases, error handling |
| `test_ammeter_framework.py` | Unit | 4 | Framework orchestration and config integration |
| `test_functional.py` | Functional | 11 | Feature behavior, data integrity, error scenarios |
| `test_error_simulation.py` | Functional/E2E | 13 | Connection errors, corrupt data, flaky connections, real emulator failure |
| `test_e2e.py` | E2E | 1 | Full pipeline: measure → save → verify JSON |
| **Total** |  | **50** |  |

### Test types explained

| Type | Emulators needed | Speed | Purpose |
| :---- | :---- | :---- | :---- |
| Smoke | Yes | Fast | Is the system alive? |
| Unit | No (mock) | Fast | Does each function work correctly? |
| Functional | Yes/Mock | Medium | Does each feature work as expected? |
| E2E | Yes | Slow | Does the full pipeline work end-to-end? |

---

## Error Simulation

`test_error_simulation.py` covers comprehensive error scenarios:

**Connection Errors (mock):**

- Connection refused — port is closed  
- Connection reset — connection drops mid-transfer  
- Timeout — ammeter does not respond in time  
- OS error — network-level failure

**Data Errors (mock):**

- None response — ammeter returns nothing  
- Corrupt data — string instead of float  
- Zero value — physically valid edge case  
- Negative value — framework accepts, statistics reflect it  
- Extreme spike — outlier detection

**Flaky Connection (mock):**

- Partial failure — some measurements succeed, some return None  
- All measurements fail — empty result list  
- Statistics on partial results — calculated only on successful measurements

**Real E2E Failure:**

- Emulator killed mid-sampling — verifies graceful handling of ConnectionRefusedError

---

## Accuracy Comparison

`compare_accuracy()` uses Coefficient of Variation (CV) to rank ammeter consistency:

CV \= (std / mean) × 100%

Lower CV \= more consistent \= more accurate.

| CV Range | Verdict |
| :---- | :---- |
| \< 10% | Excellent |
| 10% – 30% | Good |
| 30% – 60% | Moderate |
| \> 60% | Poor |

Example output:

\--- Accuracy Comparison \---

  greenlee   CV=  84.5%  (poor)

  entes      CV=  34.9%  (moderate)

  circutor   CV=  51.2%  (moderate)

  Most consistent:  entes

  Least consistent: greenlee

---

## Visualization

`run_tests.py` automatically generates a 7-panel chart saved to `results/plots/`:

- Time series per ammeter (separate subplot, own scale)  
- Measurement distribution histogram per ammeter  
- Mean ± Std Dev bar chart (log scale) for cross-ammeter comparison

---

## Ammeter Reference

| Ammeter | Port | Command | Measurement Method |
| :---- | :---- | :---- | :---- |
| Greenlee | 5000 | `MEASURE_GREENLEE -get_measurement` | Ohm's Law: I \= V / R |
| ENTES | 5001 | `MEASURE_ENTES -get_data` | Hall Effect: I \= B × K |
| CIRCUTOR | 5002 | `MEASURE_CIRCUTOR -get_measurement -current` | Rogowski Coil: I \= ∫V dt |

---

## Results

Each test run generates a JSON file in `results/` with:

- Unique `run_id` (UUID)  
- Timestamp  
- Measurements and statistics for all 3 ammeters

Example filename: `run_20260624_110724_b2e392d4.json`

Example structure:

{

  "run\_id": "b2e392d4-1234-5678-abcd-ef0123456789",

  "timestamp": "20260624\_110724",

  "results": {

    "greenlee": {

      "measurements": \[{"value": 0.117, "timestamp": 1782289375.8}\],

      "statistics": {"count": 4, "mean": 0.13, "median": 0.13, "std": 0.08, "min": 0.04, "max": 0.23}

    }

  }

}

---

## Logging

Each run generates log files in `results/logs/`:

- `YYYYMMDD_HHMMSS_pytest_run.log` — unified log for the entire pytest session (all stages, all ammeters, chronological)
- `YYYYMMDD_HHMMSS_<name>.log` — per-function log file for each AmmeterLogger call (sample, statistics, save_results)

**Note:** `ERROR` entries in log files are **expected** — they come from negative tests that verify error handling.

See `results/logs/README.md` for full log format documentation.

---

## Libraries Used

| Library | Purpose |
| :---- | :---- |
| `numpy` | Statistical calculations (mean, std, median) |
| `scipy` | Scientific computing |
| `matplotlib` | Visualization charts |
| `seaborn` | Visualization (bonus) |
| `pyyaml` | Config file parsing |
| `pandas` | Data manipulation |
| `pytest` | Testing framework |

---

## Code Examples

### Using AmmeterTestFramework (recommended)

from src.testing.test\_framework import AmmeterTestFramework

framework \= AmmeterTestFramework()  \# loads config/config.yaml automatically

\# Run a full test cycle for one ammeter

result \= framework.run\_test("greenlee")

print(result\["measurements"\])  \# \[(0.117, 1782289375.8), ...\]

print(result\["statistics"\])    \# {"count": 4, "mean": 0.13, ...}

\# Save all results to a single JSON file

results \= {

    "greenlee": framework.run\_test("greenlee"),

    "entes":    framework.run\_test("entes"),

    "circutor": framework.run\_test("circutor"),

}

saved\_path \= framework.tester.save\_results(results)

\# Compare accuracy across ammeters

accuracy \= framework.tester.compare\_accuracy(results)

print(accuracy\["ranking"\])   \# \["circutor", "entes", "greenlee"\]

print(accuracy\["details"\])   \# {"greenlee": {"cv": 84.5, "verdict": "poor"}, ...}

### Using AmmeterTester directly (lower-level)

from src.testing.ammeter\_tester import AmmeterTester

tester \= AmmeterTester()

\# Collect measurements manually

measurements \= tester.sample("greenlee", num\_measurements=4, duration=10, frequency=0.5)

\# Calculate statistics

stats \= tester.calculate\_statistics(measurements)

print(stats)  \# {"count": 4, "mean": 0.13, "median": 0.13, "std": 0.08, "min": 0.04, "max": 0.23}

\# Save results

tester.save\_results({"greenlee": {"measurements": measurements, "statistics": stats}})

---

## Design Decisions

See `CHANGES.md` for full documentation of bug fixes, design decisions, and implementation notes.  
