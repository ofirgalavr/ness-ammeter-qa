# CHANGES.md — NES Ammeter QA

Documentation of all bug fixes, design decisions, and implementation notes.

---

## Bug Fixes

### main.py — Port Numbers

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
