# CHANGES.md — NESS Ammeter QA

Documentation of all bug fixes, design decisions, and implementation notes.

---

## Bug Fixes

### `logger.py` — Stale FileHandler Bug

**Problem:** `logging.getLogger()` returns the same logger object throughout a Python process. An `if not logger.handlers:` guard prevented adding a new `FileHandler` on subsequent calls — so all runs wrote to the **first** log file created, not a new one per run.

**Fix:** Replaced the guard with an explicit loop that closes and removes all existing handlers before reconfiguring the logger.

---

### `pytest.ini` — Static `log_file` Overwrote Logs on Every Run

**Problem:** `log_file = results/logs/pytest_run.log` in `pytest.ini` caused pytest to write all session logs to a fixed filename. Each new run silently overwrote the previous log file.

**Fix:** Removed `log_file` and `log_file_level` from `pytest.ini`.

---

### `conftest.py` — Unified Per-Session Log File

**Problem:** After removing `log_file` from `pytest.ini`, there was no unified log capturing the entire pytest session.

**Fix:** Added a `pytest_configure` hook in `conftest.py` that attaches a `FileHandler` directly to the root logger at session start, creating a timestamped `YYYYMMDD_HHMMSS_pytest_run.log` file (or a single `pipeline_run.log` when invoked via `run_pipeline.sh`, see below). Every `TestLogger` instance sets `propagate = True`, so all its messages flow up into this one root-level file.

```python
def pytest_configure(config: pytest.Config) -> None:
    cfg = get_config()
    level = getattr(logging, cfg["logging"]["level"], logging.INFO)

    log_path = os.environ.get("PYTEST_LOG_FILE") or f"results/logs/{timestamp}_pytest_run.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)
```

---

### `test_smoke.py` — Smoke Tests Produced No Log Output

**Problem:** Smoke tests called `request_current_from_ammeter()` and `AmmeterTestFramework()` directly — neither uses `TestLogger` — so smoke runs produced an empty log file.

**Fix:** Added `import logging` and a module-level `logger = logging.getLogger(__name__)` to `test_smoke.py`. Each test now logs a start and result message.

---

### `ammeters/*` — Wrong Ports

**Problem:** All three ammeter ports were wrong — they did not match the ammeter objects or the README.

| Ammeter | Before | After |
|---------|-------:|------:|
| Greenlee | 5001 | 5000 |
| ENTES | 5002 | 5001 |
| CIRCUTOR | 5003 | 5002 |

**Suspected cause:** Likely a copy-paste error in the original scaffolding.

---

### `main.py` — Measurement Commands Missing Arguments

**Problem:** Commands were missing required arguments. `base_ammeter.py` does an exact string match — a partial command returns no response.

| Ammeter | Before | After |
|---------|--------|-------|
| Greenlee | `MEASURE_GREENLEE` | `MEASURE_GREENLEE -get_measurement` |
| ENTES | `MEASURE_ENTES` | `MEASURE_ENTES -get_data` |
| CIRCUTOR | `MEASURE_CIRCUTOR` | `MEASURE_CIRCUTOR -get_measurement -current` |

---

### `main.py` — Measurement Requests Were Commented Out

**Problem:** The lines that actually send measurement requests to the ammeters were commented out. The servers started but never received any requests.

**Fix:** Uncommented the request lines.

---

### `README.md` — CIRCUTOR Command Was Wrong

**Problem:** The original README listed the CIRCUTOR command as `MEASURE_CIRCUTOR -get_measurement` — missing `-current`.

**Fix:** Updated the README to match the actual command in `circutor_ammeter.py`, which is the source of truth.

---

### `client.py` — Returned Nothing

**Problem:** `client.py` printed the measurement to stdout but returned nothing. Callers had no way to use the value programmatically.

**Fix:** Changed `request_current_from_ammeter()` to return a `(value, timestamp)` tuple instead of just printing.

---

### `logger.py` — Logs Were Never Written to File

**Problem:** The logger created a Python `Logger` object but never attached a `FileHandler`. All log messages were silently discarded, and `results/logs/` was always empty.

**Fix:** Logging is now centralized: `TestLogger` sets `propagate = True` and holds no handler of its own; a single `FileHandler` is attached once, to the root logger, in `conftest.py`. This also resolved a duplicate-handler bug from an earlier version of the fix.

---

### `test_framework.py` — Missing Imports

**Problem:** `from typing import Dict` was missing, and a relative import was used instead of an absolute import, causing pytest collection to fail.

**Fix:** Added `from typing import Dict` and changed to `from src.utils.config import load_config`.

---

### `ammeter_tester.py` — Dead Variable

**Problem:** `start_time = time.time()` was assigned in `sample()` but never used.

**Fix:** Removed the unused variable.

---

### `base_ammeter.py` — Port Conflict Between Test Sessions

**Problem:** When running multiple pytest sessions sequentially (e.g., smoke then functional), the second session failed with `OSError: [Errno 48] Address already in use` because the OS had not yet released the port from the previous session.

**Fix:** Added the `SO_REUSEADDR` socket option:

```python
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```

**Why:** `SO_REUSEADDR` tells the OS to allow immediate reuse of a port after it is released, even if it is still in `TIME_WAIT` state. This lets the pipeline run multiple stages back-to-back without port conflicts.

---

## Design Decisions

### Unified API — `AMMETER_CONFIG` Dictionary

All ammeter connection details (port, command) are stored in a single dictionary in `ammeter_tester.py`:

```python
AMMETER_CONFIG = {
    "greenlee": (5000, b'MEASURE_GREENLEE -get_measurement'),
    "entes":    (5001, b'MEASURE_ENTES -get_data'),
    "circutor": (5002, b'MEASURE_CIRCUTOR -get_measurement -current'),
}
```

**Why:** Adding a new ammeter type requires changing only this dictionary — no other code changes needed. This keeps the framework easy to extend.

---

### Error Handling — `logger.error` + `raise ValueError`

All validation errors follow the same pattern:

```python
logger.error("descriptive message")
raise ValueError("descriptive message")
```

**Why:** Silent failures (returning `[]` or `None`) hide bugs. Raising an exception forces the caller to handle the error explicitly. Logging first ensures the error is always recorded to file even if the exception is caught upstream.

---

### Sampling — Consistency Validation

`sample()` validates that `num_measurements <= duration * frequency` before starting.

**Why:** Inconsistent parameters (e.g., asking for 100 measurements in 10 seconds at 0.5 Hz) would cause the test to run indefinitely or produce wrong results. Failing fast with a clear error message is better than silently producing bad data.

---

### `save_results` — One JSON File Per Run

All three ammeters are saved in a single JSON file per run, identified by a UUID:

```python
run_id = str(uuid.uuid4())
filename = f"{output_dir}/run_{timestamp}_{run_id[:8]}.json"
```

**Why:** A single file per run makes it easy to compare results across ammeters for the same test session. Separate files per ammeter would require joining them manually to reconstruct a run. The same `run_id` is asserted as unique between runs in `test_functional.py::test_run_id_is_unique_between_runs`.

---

### `test_framework.py` — Configuration-Driven Orchestrator

`AmmeterTestFramework.run_test()` reads all sampling parameters from `config.yaml`:

```python
sampling = self.config["testing"]["sampling"]
num_measurements = sampling["measurements_count"]
duration         = sampling["total_duration_seconds"]
frequency        = sampling["sampling_frequency_hz"]
```

**Why:** Changing test parameters requires editing only `config.yaml` — no code changes needed. This satisfies the bonus requirement for a configuration-driven testing approach.

---

### Testing Strategy — Four Layers

Tests are organized into four layers that run in order:

| Layer | File(s) | Emulators | Purpose |
|-------|---------|-----------|---------|
| Smoke | `test_smoke.py` | Yes | Is the system alive? |
| Unit | `test_ammeter_tester.py`, `test_ammeter_framework.py` | No (mock) | Does each function work? |
| Functional | `test_functional.py`, `test_error_simulation.py` | Yes / Mock | Does each feature work as expected? |
| E2E | `test_e2e.py` | Yes | Does the full pipeline work? |

**Why:** Unit tests run without emulators — fast and reliable. Functional tests verify behavior with real data. E2E verifies the complete flow. Smoke tests catch startup failures before running anything else.

---

### `conftest.py` — Session-Scoped Emulators

Emulators are started once per pytest session using a session-scoped fixture:

```python
@pytest.fixture(scope="session")
def live_framework():
    start_emulators()
    # wait for ports...
    yield AmmeterTestFramework()
    # teardown: daemon threads shut down automatically
```

**Why:** Starting emulators in each test file caused port conflicts (`OSError: Address already in use`). A single session-scoped fixture ensures emulators start once and are shared across all test files.

---

### PEP 8 Compliance — Package and Module Renaming

All package and module names were updated to follow PEP 8's lowercase convention:

| Before | After |
|--------|-------|
| `Ammeters/` | `ammeters/` |
| `Ammeters/Greenlee_Ammeter.py` | `ammeters/greenlee_ammeter.py` |
| `Ammeters/Entes_Ammeter.py` | `ammeters/entes_ammeter.py` |
| `Ammeters/Circutor_Ammeter.py` | `ammeters/circutor_ammeter.py` |
| `src/testing/AmmeterTester.py` | `src/testing/ammeter_tester.py` |
| `src/utils/Utils.py` | `src/utils/utils.py` |

**Why:** PEP 8 states that package and module names should be lowercase. Class names remain CamelCase (`AmmeterTester`, `CircutorAmmeter`) per convention. This also fixed a real cross-platform bug: macOS's case-insensitive filesystem let inconsistent casing pass silently, while Python's import system — and Linux's filesystem — are both case-sensitive. The project now runs identically on macOS and Linux.

---

### Visualization — `visualizer.py`

`src/utils/visualizer.py` generates a 7-panel chart from test results:

- **Rows 1–3:** Time series per ammeter (separate subplot, own Y-axis scale)
- **Rows 4–6:** Measurement distribution histogram per ammeter (own X-axis scale)
- **Row 7:** Mean ± Std Dev bar chart with log scale, for cross-ammeter comparison

**Why separate subplots per ammeter?** The three ammeters operate on completely different scales (Greenlee: ~0.1 A, ENTES: ~50–100 A, CIRCUTOR: ~0.03 A). A shared Y-axis would make two of the three ammeters invisible. Each ammeter gets its own scale so all data is clearly visible.

**Why log scale on the bar chart?** Same reason — log scale allows meaningful visual comparison between values that differ by three orders of magnitude.

---

### Accuracy Comparison — `compare_accuracy()`

`compare_accuracy()` uses Coefficient of Variation (CV) to rank ammeter consistency:

```
CV = (std / mean) × 100%
```

**Why CV instead of std?** `std` alone is not comparable across ammeters with different scales. A std of 20 A on ENTES (mean ~70 A) is less concerning than a std of 0.1 A on Greenlee (mean ~0.13 A). CV normalizes std relative to the mean, enabling a fair comparison.

| CV Range | Verdict |
|----------|---------|
| < 10% | Excellent |
| 10%–30% | Good |
| 30%–60% | Moderate |
| > 60% | Poor |

---

### Error Simulation — `test_error_simulation.py`

Comprehensive error simulation covering four categories:

1. **Connection Errors (mock):** `ConnectionRefusedError`, `ConnectionResetError`, `socket.timeout`, `OSError` — verifies all network-level errors propagate correctly.
2. **Data Errors (mock):** `None` response, corrupt data, zero value, negative value, extreme spike — verifies the framework handles invalid data without crashing.
3. **Flaky Connection (mock):** Partial failures, all failures, statistics on partial results — verifies graceful degradation when some measurements fail.
4. **Real E2E Failure:** A limited emulator that stops accepting connections after 2 requests simulates a real mid-sampling failure. The framework must handle `ConnectionRefusedError` gracefully and return whatever measurements were collected before the failure.

**Why mock for categories 1–3?** Mock tests are fast, deterministic, and test specific failure modes in isolation. Real emulators introduce timing dependencies and are harder to control.

**Why real E2E for category 4?** To verify that the complete stack (socket → client → `sample()` → error handling) behaves correctly under an actual failure, not just a simulated one.

---

### Test Pipeline — `run_pipeline.sh`

`tests/run_pipeline.sh` runs tests in stages with configurable arguments:

```bash
./tests/run_pipeline.sh                  # Full pipeline
./tests/run_pipeline.sh smoke unit       # Specific stages
./tests/run_pipeline.sh functional e2e   # Specific stages
```

**Stage failure behavior:**

- `smoke` and `unit` — stop the pipeline immediately; if core logic is broken, there is no point running integration tests
- `functional` and `e2e` — continue on failure and collect a full report across all feature tests

**Why markers instead of file names?** Using `-m smoke`, `-m unit`, etc. means new test files are automatically included in the correct stage as long as they use the right marker. No need to update the pipeline script when adding new test files.

**Note on `deselected`:** When running by marker, pytest collects all tests and then filters. `deselected` in the output indicates tests skipped due to marker filtering — this is expected and correct behavior.

---

## Libraries Added

| Library | Reason |
|---------|--------|
| `pytest` | Testing framework — required for the test suite |
| `numpy` | Statistical calculations (mean, std with `ddof=1`, median, min, max) |

All other libraries (`scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pandas`) were already in `requirements.txt`.
