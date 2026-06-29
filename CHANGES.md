# CHANGES.md — NESS Ammeter QA

Documentation of all bug fixes, design decisions, and implementation notes.

---

## Bug Fixes — Session 2 (25/06/2026)

### logger.py — Stale FileHandler Bug

**Problem:** `logging.getLogger()` returns the same logger object throughout a Python process. The `if not logger.handlers:` guard prevented adding a new `FileHandler` on subsequent calls — so all runs wrote to the **first** log file created, not a new one per run.

**Fix:** Replaced the guard with an explicit loop that closes and removes all existing handlers before adding a fresh `FileHandler` with the current timestamp.

---

### pytest.ini — Static log_file Overwrote Logs on Every Run

**Problem:** `log_file = results/logs/pytest_run.log` in `pytest.ini` caused pytest to write all session logs to a fixed filename. Each new run silently overwrote the previous log file.

**Fix:** Removed `log_file` and `log_file_level` from `pytest.ini`.

---

### conftest.py — Unified Per-Session Log File

**Problem:** After removing `log_file` from `pytest.ini`, there was no unified log capturing the entire pytest session.

**Fix:** Added `pytest_configure` hook in `conftest.py` that attaches a `FileHandler` directly to the root logger at session start, creating a timestamped `YYYYMMDD_HHMMSS_pytest_run.log` file. All `AmmeterLogger` messages flow into it via `propagate=True`.

---

### test_smoke.py — Smoke Tests Produced No Log Output

**Problem:** Smoke tests called `request_current_from_ammeter()` and `AmmeterTestFramework()` directly — neither uses `AmmeterLogger` — so smoke runs produced an empty `pytest_run.log`.

**Fix:** Added `import logging` and a module-level `logger = logging.getLogger(__name__)` to `test_smoke.py`. Each test now logs start and result messages.


**Problem:** All three ammeter ports were wrong — they did not match the ammeter objects or the README.

| Ammeter | Before | After |
| :---- | :---- | :---- |
| Greenlee | 5001 | 5000 |
| ENTES | 5002 | 5001 |
| CIRCUTOR | 5003 | 5002 |

**Suspected cause:** Likely a copy-paste error in the original scaffolding.

---

### main.py — Measurement Commands

**Problem:** Commands were missing required arguments. `base_ammeter.py` does an exact string match — a partial command returns no response.

| Ammeter | Before | After |
| :---- | :---- | :---- |
| Greenlee | `MEASURE_GREENLEE` | `MEASURE_GREENLEE -get_measurement` |
| ENTES | `MEASURE_ENTES` | `MEASURE_ENTES -get_data` |
| CIRCUTOR | `MEASURE_CIRCUTOR` | `MEASURE_CIRCUTOR -get_measurement -current` |

---

### main.py — Measurement Requests Were Commented Out

**Problem:** The lines that actually send measurement requests to the ammeters were commented out with `#`. The servers started but never received any requests.

**Fix:** Uncommented the request lines.

---

### README.md — Circutor Command Was Wrong

**Problem:** The original README listed the Circutor command as `MEASURE_CIRCUTOR -get_measurement` — missing `-current`.

**Fix:** Updated README to match the actual command in `Circutor_Ammeter.py`, which is the source of truth.

---

### client.py — Returned Nothing

**Problem:** `client.py` printed the measurement to stdout but returned nothing. Callers had no way to use the value programmatically.

**Fix:** Changed `request_current_from_ammeter()` to return `(value, timestamp)` tuple instead of just printing.

---

### logger.py — Logs Were Never Written to File

**Problem:** `TestLogger` created a logger but never added a `FileHandler`. All log messages were silently discarded. The `results/logs/` directory was always empty.

**Fix:** Added `FileHandler`, `setLevel(INFO)`, `propagate=False`, and duplicate handler prevention.

---

### test\_framework.py — Missing Imports

**Problem:** `from typing import Dict` was missing, and a relative import was used instead of an absolute import, causing pytest collection to fail.

**Fix:** Added `from typing import Dict` and changed to `from src.utils.config import load_config`.

---

### AmmeterTester.py — Dead Variable

**Problem:** `start_time = time.time()` was assigned in `sample()` but never used.

**Fix:** Removed the unused variable.

---

## Design Decisions

### Unified API — AMMETER\_CONFIG Dictionary

All ammeter connection details (port, command) are stored in a single dictionary in `AmmeterTester.py`:

AMMETER\_CONFIG \= {

    "greenlee": (5000, b'MEASURE\_GREENLEE \-get\_measurement'),

    "entes":    (5001, b'MEASURE\_ENTES \-get\_data'),

    "circutor": (5002, b'MEASURE\_CIRCUTOR \-get\_measurement \-current'),

}

**Why:** Adding a new ammeter type requires changing only this dictionary — no other code changes needed. This makes the framework easy to extend.

---

### Error Handling — logger.error \+ raise ValueError

All validation errors follow the same pattern:

logger.error("descriptive message")

raise ValueError("descriptive message")

**Why:** Silent failures (returning `[]` or `None`) hide bugs. Raising an exception forces the caller to handle the error explicitly. The logger ensures the error is always recorded to file even if the exception is caught upstream.

---

### Sampling — Consistency Validation

`sample()` validates that `num_measurements <= duration * frequency` before starting.

**Why:** Inconsistent parameters (e.g., asking for 100 measurements in 10 seconds at 0.5 Hz) would cause the test to run indefinitely or produce wrong results. Failing fast with a clear error message is better than silently producing bad data.

---

### save\_results — One JSON File Per Run

All three ammeters are saved in a single JSON file per run, identified by a UUID.

**Why:** A single file per run makes it easy to compare results across ammeters for the same test session. Separate files per ammeter would require joining them manually to reconstruct a run.

---

### test\_framework.py — Configuration-Driven Orchestrator

`AmmeterTestFramework.run_test()` reads all sampling parameters from `config.yaml`:

sampling \= self.config\["testing"\]\["sampling"\]

num\_measurements \= sampling\["measurements\_count"\]

duration \= sampling\["total\_duration\_seconds"\]

frequency \= sampling\["sampling\_frequency\_hz"\]

**Why:** Changing test parameters requires editing only `config.yaml` — no code changes needed. This satisfies the bonus requirement for a configuration-driven testing approach.

---

### Testing Strategy — Four Layers

Tests are organized into four layers that run in order:

| Layer | File | Emulators | Purpose |
| :---- | :---- | :---- | :---- |
| Smoke | `test_smoke.py` | Yes | Is the system alive? |
| Unit | `test_ammeter_tester.py`, `test_ammeter_framework.py` | No (mock) | Does each function work? |
| Functional | `test_functional.py` | Yes | Does each feature work as expected? |
| E2E | `test_e2e.py` | Yes | Does the full pipeline work? |

**Why:** Unit tests run without emulators — fast and reliable. Functional tests verify behavior with real data. E2E verifies the complete flow. Smoke tests catch startup failures before running anything else.

---

### conftest.py — Session-Scoped Emulators

Emulators are started once per pytest session in `conftest.py` using a session-scoped fixture:

@pytest.fixture(scope="session")

def live\_framework():

    start\_emulators()

    \# wait for ports...

    yield AmmeterTestFramework()

    \# teardown: daemon threads shut down automatically

**Why:** Starting emulators in each test file caused port conflicts (`OSError: Address already in use`). A single session-scoped fixture ensures emulators start once and are shared across all test files.

---

## Libraries Added

| Library | Reason |
| :---- | :---- |
| `pytest` | Testing framework — required for the test suite |
| `numpy` | Statistical calculations (mean, std with ddof=1, median, min, max) |

All other libraries (`scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pandas`) were already in `requirements.txt`.

---

## Additional Bug Fixes

### base\_ammeter.py — Port Conflict Between Test Sessions

**Problem:** When running multiple pytest sessions sequentially (e.g., smoke then functional), the second session failed with `OSError: [Errno 48] Address already in use` because the OS had not yet released the port from the previous session.

**Fix:** Added `SO_REUSEADDR` socket option to `base_ammeter.py`:

s.setsockopt(socket.SOL\_SOCKET, socket.SO\_REUSEADDR, 1\)

**Why:** `SO_REUSEADDR` tells the OS to allow immediate reuse of a port after it is released, even if it is still in `TIME_WAIT` state. This enables the pipeline to run multiple sessions without port conflicts.

---

### logger.py — Class Name Conflicted with pytest Collection

**Problem:** pytest tried to collect `TestLogger` as a test class because its name starts with `Test`, causing a `PytestCollectionWarning` on every run.

**Fix:** Added `__test__ = False` to `logger.py` and renamed the class from `TestLogger` to `AmmeterLogger`.

**Why:** PEP 8 and pytest convention: test classes start with `Test`. A logger class should not follow this naming. Renaming to `AmmeterLogger` is semantically correct and eliminates the warning.

---

## Additional Design Decisions

### PEP 8 Compliance — Package and Module Renaming

All package and module names were updated to follow PEP 8 lowercase convention:

| Before | After |
| :---- | :---- |
| `Ammeters/` | `ammeters/` |
| `Ammeters/Greenlee_Ammeter.py` | `ammeters/greenlee_ammeter.py` |
| `Ammeters/Entes_Ammeter.py` | `ammeters/entes_ammeter.py` |
| `Ammeters/Circutor_Ammeter.py` | `ammeters/circutor_ammeter.py` |
| `src/testing/AmmeterTester.py` | `src/testing/ammeter_tester.py` |

**Why:** PEP 8 states that package and module names should be lowercase. Class names remain CamelCase (`AmmeterTester`, `CircutorAmmeter`) as per convention.

---

### Visualization — visualizer.py

`src/utils/visualizer.py` generates a 7-panel chart from test results:

- **Rows 1–3:** Time series per ammeter (separate subplot, own Y-axis scale)  
- **Rows 4–6:** Measurement distribution histogram per ammeter (own X-axis scale)  
- **Row 7:** Mean ± Std Dev bar chart with log scale for cross-ammeter comparison

**Why separate subplots per ammeter?** The three ammeters operate on completely different scales (Greenlee: \~0.1A, ENTES: \~50–100A, Circutor: \~0.03A). A shared Y-axis would make two of the three ammeters invisible. Each ammeter gets its own scale so all data is clearly visible.

**Why log scale on the bar chart?** Same reason — log scale allows meaningful visual comparison between values that differ by 3 orders of magnitude.

---

### Accuracy Comparison — compare\_accuracy()

`compare_accuracy()` uses Coefficient of Variation (CV) to rank ammeter consistency:

CV \= (std / mean) × 100%

**Why CV instead of std?** `std` alone is not comparable across ammeters with different scales. A std of 20A on ENTES (mean \~70A) is less concerning than a std of 0.1A on Greenlee (mean \~0.13A). CV normalizes std relative to the mean, enabling fair comparison.

| CV Range | Verdict |
| :---- | :---- |
| \< 10% | Excellent |
| 10%–30% | Good |
| 30%–60% | Moderate |
| \> 60% | Poor |

---

### Error Simulation — test\_error\_simulation.py

Comprehensive error simulation covering 4 categories:

**1\. Connection Errors (mock):** ConnectionRefusedError, ConnectionResetError, socket.timeout, OSError — verifies all network-level errors propagate correctly.

**2\. Data Errors (mock):** None response, corrupt data, zero value, negative value, extreme spike — verifies the framework handles invalid data without crashing.

**3\. Flaky Connection (mock):** Partial failures, all failures, statistics on partial results — verifies graceful degradation when some measurements fail.

**4\. Real E2E Failure:** A limited emulator that stops after 2 connections simulates a real mid-sampling failure. The framework must handle `ConnectionRefusedError` gracefully and return whatever measurements were collected before the failure.

**Why mock for categories 1–3?** Mock tests are fast, deterministic, and test specific failure modes in isolation. Real emulators introduce timing dependencies and are harder to control.

**Why real E2E for category 4?** To verify that the complete stack (socket → client → sample() → error handling) behaves correctly under a real failure scenario, not just a simulated one.

---

### Test Pipeline — run\_pipeline.sh

`tests/run_pipeline.sh` runs tests in stages with configurable arguments:

./tests/run\_pipeline.sh                  \# Full pipeline

./tests/run\_pipeline.sh smoke unit       \# Specific stages

./tests/run\_pipeline.sh functional e2e   \# Specific stages

**Stage failure behavior:**

- `smoke` and `unit`: stop pipeline immediately — if core logic is broken, there is no point running integration tests  
- `functional` and `e2e`: continue on failure — collect a full report across all feature tests

**Why markers instead of file names?** Using `-m smoke`, `-m unit` etc. means new test files are automatically included in the correct stage as long as they use the right marker. No need to update the pipeline script when adding new test files.

**Note on `deselected`:** When running by marker, pytest collects all tests and filters. `deselected` in the output indicates tests skipped due to marker filtering — this is expected and correct behavior.

---

### Per-Run Logging — Shared run\_id

`AmmeterLogger` accepts an optional `run_id` parameter. When provided, all logs from a single test session are written to one file named `run_<timestamp>_<run_id[:8]>.log`, matching the corresponding JSON result file.

**Why:** Without a shared run\_id, each function call created a separate log file, making it impossible to trace a complete test session across `sample()`, `calculate_statistics()`, and `save_results()`. A shared run\_id links all logs to the JSON result file for the same run.

**Two log file types:**

- `pytest_run.log` — all unit test logs (no run\_id)  
- `run_<id>.log` — functional/E2E logs linked to a specific result JSON

