# NES Ammeter QA — Testing Framework

A Python-based testing framework for current measurement systems using multiple ammeter types (Greenlee, ENTES, CIRCUTOR). Built as part of a technical home assignment for NES.

---

## Project Structure

Test\_QA\_expanded/

├── main.py                        \# Starts all 3 ammeters and requests measurements

├── config/

│   └── config.yaml                \# Sampling, ammeter, and analysis configuration

├── Ammeters/

│   ├── base\_ammeter.py            \# Base TCP socket server for all ammeters

│   ├── Greenlee\_Ammeter.py        \# Ohm's Law emulator (port 5000\)

│   ├── Entes\_Ammeter.py           \# Hall Effect emulator (port 5001\)

│   ├── Circutor\_Ammeter.py        \# Rogowski Coil emulator (port 5002\)

│   └── client.py                  \# TCP client for measurement requests

├── src/

│   ├── testing/

│   │   ├── AmmeterTester.py       \# Unified API: sample, statistics, save results

│   │   └── test\_framework.py      \# Orchestrator: runs full test cycle from config

│   └── utils/

│       ├── config.py              \# Loads config.yaml

│       ├── logger.py              \# Writes logs to results/logs/

│       └── Utils.py               \# Utility functions

├── examples/

│   └── run\_tests.py               \# Demo: runs all 3 ammeters and saves results

├── tests/

│   ├── conftest.py                \# Shared fixtures \+ session-scoped emulator startup

│   ├── test\_smoke.py              \# Smoke tests (2 tests)

│   ├── test\_ammeter\_tester.py     \# Unit tests for AmmeterTester (19 tests)

│   ├── test\_ammeter\_framework.py  \# Unit tests for AmmeterTestFramework (4 tests)

│   ├── test\_functional.py         \# Functional tests (11 tests)

│   └── test\_e2e.py                \# End-to-end test (1 test)

├── results/                       \# Auto-generated JSON result files

│   └── logs/                      \# Auto-generated log files

├── pytest.ini                     \# pytest configuration and markers

└── requirements.txt               \# Python dependencies

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

Starts all 3 ammeter emulators, collects measurements, calculates statistics, and saves results to `results/`.

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

### Full test pipeline (recommended)

Runs all tests in order — smoke → unit → functional → e2e. Emulators start once and are shared across all tests.

./venv/bin/python3 \-m pytest tests/test\_smoke.py tests/test\_ammeter\_tester.py tests/test\_ammeter\_framework.py tests/test\_functional.py tests/test\_e2e.py \-v

### Run by marker

./venv/bin/python3 \-m pytest tests/ \-v \-m smoke        \# Sanity check only

./venv/bin/python3 \-m pytest tests/ \-v \-m unit         \# Unit tests only (no emulators)

./venv/bin/python3 \-m pytest tests/ \-v \-m functional   \# Functional tests

./venv/bin/python3 \-m pytest tests/ \-v \-m e2e          \# End-to-end test

### Test coverage summary

| File | Type | Tests | Description |
| :---- | :---- | :---- | :---- |
| `test_smoke.py` | Smoke | 2 | System starts and responds |
| `test_ammeter_tester.py` | Unit | 19 | Validations, happy path, edge cases, error handling |
| `test_ammeter_framework.py` | Unit | 4 | Framework orchestration and config integration |
| `test_functional.py` | Functional | 11 | Feature behavior, data integrity, error scenarios |
| `test_e2e.py` | E2E | 1 | Full pipeline: measure → save → verify JSON |
| **Total** |  | **37** |  |

### Test types explained

| Type | Emulators needed | Speed | Purpose |
| :---- | :---- | :---- | :---- |
| Smoke | Yes | Fast | Is the system alive? |
| Unit | No (mock) | Fast | Does each function work correctly? |
| Functional | Yes | Medium | Does each feature work as expected? |
| E2E | Yes | Slow | Does the full pipeline work end-to-end? |

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

  "run\_id": "b2e392d4-...",

  "timestamp": "20260624\_110724",

  "results": {

    "greenlee": {

      "measurements": \[{"value": 1.23, "timestamp": 1782288420.3}\],

      "statistics": {"count": 4, "mean": 0.93, "median": 0.38, "std": 1.36, "min": 0.03, "max": 2.93}

    }

  }

}

---

## Libraries Installed

| Library | Purpose |
| :---- | :---- |
| `numpy` | Statistical calculations (mean, std, median) |
| `scipy` | Scientific computing |
| `matplotlib` | Visualization (bonus) |
| `seaborn` | Visualization (bonus) |
| `pyyaml` | Config file parsing |
| `pandas` | Data manipulation |
| `pytest` | Testing framework |

---

## Design Decisions

See `CHANGES.md` for full documentation of bug fixes, design decisions, and implementation notes.  
