# NESS Ammeter QA — Testing Framework

A Python-based testing framework for current measurement systems using multiple ammeter types (Greenlee, ENTES, CIRCUTOR). Built as part of a technical home assignment for NESS.

---

## About the Assignment

The original assignment provided three TCP-based ammeter emulators (Greenlee, ENTES, CIRCUTOR), each simulating a different physical measurement method and responding to measurement requests over sockets. The task: build a complete QA testing framework around them — collect samples, compute statistics, persist results, and verify system behavior including error scenarios.

This repository contains the original emulators plus the testing framework built on top of them: a 4-stage test pipeline (50 tests), unified logging, accuracy comparison, and results visualization.

---

## Project Structure

```
ness-ammeter-qa/
├── main.py                        # Starts all 3 ammeters and requests measurements
├── config/
│   └── config.yaml                # Sampling, ammeter, and logging configuration
├── ammeters/                      # PEP 8 compliant package (lowercase)
│   ├── base_ammeter.py            # Base TCP socket server for all ammeters
│   ├── greenlee_ammeter.py        # Ohm's Law emulator (port 5000)
│   ├── entes_ammeter.py           # Hall Effect emulator (port 5001)
│   ├── circutor_ammeter.py        # Rogowski Coil emulator (port 5002)
│   └── client.py                  # TCP client for measurement requests
├── src/
│   ├── testing/
│   │   ├── ammeter_tester.py      # Unified API: sample, statistics, save results, compare accuracy
│   │   └── test_framework.py      # Orchestrator: runs full test cycle from config
│   └── utils/
│       ├── config.py              # Loads config.yaml
│       ├── logger.py              # Propagates test logs to the unified pipeline log
│       ├── visualizer.py          # Generates charts from results (bonus)
│       └── utils.py               # Helper functions (random value generation)
├── examples/
│   └── run_tests.py               # Demo: runs all 3 ammeters, saves results, plots charts
├── tests/
│   ├── conftest.py                # Shared fixtures + session-scoped emulator startup
│   ├── run_pipeline.sh            # Test pipeline script with stage control
│   ├── test_smoke.py              # Smoke tests (2 tests)
│   ├── test_ammeter_tester.py     # Unit tests for AmmeterTester (19 tests)
│   ├── test_ammeter_framework.py  # Unit tests for AmmeterTestFramework (4 tests)
│   ├── test_functional.py         # Functional tests (11 tests)
│   ├── test_error_simulation.py   # Error simulation tests (13 tests)
│   └── test_e2e.py                # End-to-end test (1 test)
├── Exam/                          # Original assignment specification
├── results/                       # Auto-generated at runtime (not in repo)
│   ├── logs/                      # Unified pipeline / pytest log files
│   └── plots/                     # Visualization charts
├── CHANGES.md                     # Bug fixes, design decisions, implementation notes
├── pytest.ini                     # pytest configuration and markers
└── requirements.txt               # Python dependencies
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/ofirgalavr/ness-ammeter-qa.git

# Navigate to the project directory
cd ness-ammeter-qa

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Run the demo (all 3 ammeters)

```bash
python3 -m examples.run_tests
```

Starts all 3 ammeter emulators, collects measurements, calculates statistics, saves results to `results/`, generates visualization charts, and prints accuracy comparison.

### Run a quick measurement check

```bash
python3 main.py
```

---

## Configuration

Edit `config/config.yaml` to control sampling behavior:

```yaml
testing:
  sampling:
    measurements_count: 4        # Number of measurements per run
    total_duration_seconds: 10   # Total test duration
    sampling_frequency_hz: 0.5   # Measurements per second
```

---

## Data Flow

The following shows the full data flow for a single ammeter test run:

```
config.yaml
    ↓  (measurements_count=4, duration=10, frequency=0.5)
AmmeterTestFramework.run_test("greenlee")
    ↓
AmmeterTester.sample("greenlee", 4, 10, 0.5)
    ↓  [4 times, every 2 seconds]
client.request_current_from_ammeter(5000, b'MEASURE_GREENLEE -get_measurement')
    ↓
[(0.12, 1782289375.8), (0.08, 1782289377.8), (0.15, 1782289379.8), (0.11, 1782289381.8)]
    ↓
AmmeterTester.calculate_statistics(measurements)
    ↓
{"count": 4, "mean": 0.115, "std": 0.03, "min": 0.08, "max": 0.15, ...}
    ↓
AmmeterTester.save_results(results)
    ↓
results/run_20260624_110724_b2e392d4.json
```

---

## Testing

### Run the full pipeline (recommended)

```bash
./tests/run_pipeline.sh
```

Runs all stages in order: smoke → unit → functional → e2e.

- **smoke** and **unit** stop the pipeline immediately on failure
- **functional** and **e2e** continue on failure and show a full summary

### Run specific stages

```bash
./tests/run_pipeline.sh smoke            # Smoke only
./tests/run_pipeline.sh unit             # Unit only
./tests/run_pipeline.sh functional       # Functional only
./tests/run_pipeline.sh e2e              # E2E only
./tests/run_pipeline.sh smoke unit       # Smoke then unit
./tests/run_pipeline.sh functional e2e   # Functional then e2e
```

### Run by marker

```bash
./venv/bin/python3 -m pytest tests/ -v -m smoke        # Sanity check only
./venv/bin/python3 -m pytest tests/ -v -m unit         # Unit tests only (no emulators)
./venv/bin/python3 -m pytest tests/ -v -m functional   # Functional tests
./venv/bin/python3 -m pytest tests/ -v -m e2e          # End-to-end test
```

> **Note:** When running by marker, pytest collects all tests and filters by marker. `deselected` in the output indicates tests skipped due to marker filtering — this is expected behavior.

### Test coverage summary

| File | Type | Tests | Description |
|------|------|------:|-------------|
| `test_smoke.py` | Smoke | 2 | System starts and responds |
| `test_ammeter_tester.py` | Unit | 19 | Validations, happy path, edge cases, error handling |
| `test_ammeter_framework.py` | Unit | 4 | Framework orchestration and config integration |
| `test_functional.py` | Functional | 11 | Feature behavior, data integrity, error scenarios |
| `test_error_simulation.py` | Functional/E2E | 13 | Connection errors, corrupt data, flaky connections, real emulator failure |
| `test_e2e.py` | E2E | 1 | Full pipeline: measure → save → verify JSON |
| **Total** | | **50** | |

### Test types explained

| Type | Emulators needed | Speed | Purpose |
|------|------------------|-------|---------|
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

- Emulator killed mid-sampling — verifies graceful handling of `ConnectionRefusedError`

---

## Accuracy Comparison

`compare_accuracy()` uses Coefficient of Variation (CV) to rank ammeter consistency:

```
CV = (std / mean) × 100%
```

Lower CV = more consistent = more accurate.

| CV Range | Verdict |
|----------|---------|
| < 10% | Excellent |
| 10% – 30% | Good |
| 30% – 60% | Moderate |
| > 60% | Poor |

Example output:

```
--- Accuracy Comparison ---
  greenlee   CV=  84.5%  (poor)
  entes      CV=  34.9%  (moderate)
  circutor   CV=  51.2%  (moderate)

  Most consistent:  entes
  Least consistent: greenlee
```

---

## Visualization

`run_tests.py` automatically generates a 7-panel chart saved to `results/plots/`:

- Time series per ammeter (separate subplot, own scale)
- Measurement distribution histogram per ammeter
- Mean ± Std Dev bar chart (log scale) for cross-ammeter comparison

---

## Ammeter Reference

| Ammeter | Port | Command | Measurement Method | Simulated Ranges |
|---------|-----:|---------|--------------------|------------------|
| Greenlee | 5000 | `MEASURE_GREENLEE -get_measurement` | Ohm's Law: I = V / R | V: 1–10 V, R: 0.1–100 Ω |
| ENTES | 5001 | `MEASURE_ENTES -get_data` | Hall Effect: I = B × K | B: 0.01–0.1 T, K: 500–2000 |
| CIRCUTOR | 5002 | `MEASURE_CIRCUTOR -get_measurement -current` | Rogowski Coil: I = ∫V dt | V: 0.1–1.0 V, dt: 0.001–0.01 s |

---

## Results

Each test run generates a JSON file in the directory defined by `result_management.output_dir` in `config.yaml` (default: `results/`) with:

- Unique `run_id` (UUID)
- Timestamp
- Measurements and statistics for all 3 ammeters

Example filename: `run_20260624_110724_b2e392d4.json`

Example structure:

```json
{
  "run_id": "b2e392d4-1234-5678-abcd-ef0123456789",
  "timestamp": "20260624_110724",
  "results": {
    "greenlee": {
      "measurements": [{"value": 0.117, "timestamp": 1782289375.8}],
      "statistics": {"count": 4, "mean": 0.13, "median": 0.13, "std": 0.08, "min": 0.04, "max": 0.23}
    }
  }
}
```

---

## Logging

The `results/logs/` directory is created automatically on first run. Each pipeline run generates a **single unified log file**:

- `YYYYMMDD_HHMMSS_pipeline_run.log` — one file per pipeline run, containing all stages (smoke → unit → functional → e2e), all ammeters, and all test results in chronological order

Log level is controlled via `config.yaml` — change it in one place to affect all loggers:

```yaml
logging:
  level: "INFO"  # Change to WARNING or ERROR to reduce output
```

When running pytest directly (without `run_pipeline.sh`), a `YYYYMMDD_HHMMSS_pytest_run.log` file is created instead.

> **Note:** `ERROR` entries in log files are **expected** — they come from negative tests that verify error handling.

---

## Libraries Used

| Library | Purpose |
|---------|---------|
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

```python
from src.testing.test_framework import AmmeterTestFramework

framework = AmmeterTestFramework()  # loads config/config.yaml automatically

# Run a full test cycle for one ammeter
result = framework.run_test("greenlee")
print(result["measurements"])  # [(0.117, 1782289375.8), ...]
print(result["statistics"])    # {"count": 4, "mean": 0.13, ...}

# Save all results to a single JSON file
results = {
    "greenlee": framework.run_test("greenlee"),
    "entes":    framework.run_test("entes"),
    "circutor": framework.run_test("circutor"),
}
saved_path = framework.tester.save_results(results)

# Compare accuracy across ammeters
accuracy = framework.tester.compare_accuracy(results)
print(accuracy["ranking"])   # ["circutor", "entes", "greenlee"]
print(accuracy["details"])   # {"greenlee": {"cv": 84.5, "verdict": "poor"}, ...}
```

### Using AmmeterTester directly (lower-level)

```python
from src.testing.ammeter_tester import AmmeterTester

tester = AmmeterTester()

# Collect measurements manually
measurements = tester.sample("greenlee", num_measurements=4, duration=10, frequency=0.5)

# Calculate statistics
stats = tester.calculate_statistics(measurements)
print(stats)  # {"count": 4, "mean": 0.13, "median": 0.13, "std": 0.08, "min": 0.04, "max": 0.23}

# Save results
tester.save_results({"greenlee": {"measurements": measurements, "statistics": stats}})
```

---

## Design Decisions

See `CHANGES.md` for full documentation of bug fixes, design decisions, and implementation notes.
