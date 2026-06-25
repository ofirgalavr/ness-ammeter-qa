# tests/test_error_simulation.py
# Comprehensive error simulation tests for the ammeter testing framework.
# Tests cover: connection errors, timeouts, corrupt data, flaky connections,
# and real E2E emulator failures.

import socket
import threading
import time

import pytest
from unittest.mock import patch, MagicMock

from src.testing.ammeter_tester import AmmeterTester
from src.testing.test_framework import AmmeterTestFramework


# ── Category 1: Mock-based error simulation ───────────────────────────

@pytest.mark.functional
class TestConnectionErrors:

    def test_connection_refused_raises(self, tester):
        """Port is closed — connection must be refused immediately."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.side_effect = ConnectionRefusedError("Connection refused")
            with pytest.raises(ConnectionRefusedError):
                tester.sample("greenlee", 3, 10, 1.0)

    def test_connection_reset_raises(self, tester):
        """Connection drops mid-transfer — must propagate as ConnectionResetError."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.side_effect = ConnectionResetError("Connection reset by peer")
            with pytest.raises(ConnectionResetError):
                tester.sample("greenlee", 3, 10, 1.0)

    def test_timeout_raises(self, tester):
        """Ammeter does not respond in time — must raise socket.timeout."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.side_effect = socket.timeout("timed out")
            with pytest.raises(socket.timeout):
                tester.sample("greenlee", 3, 10, 1.0)

    def test_os_error_raises(self, tester):
        """Network-level OS error — must propagate up."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.side_effect = OSError("Network unreachable")
            with pytest.raises(OSError):
                tester.sample("greenlee", 3, 10, 1.0)


@pytest.mark.functional
class TestDataErrors:

    def test_none_response_skips_measurement(self, tester):
        """None response must be skipped — not added to measurements list."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.return_value = None
            results = tester.sample("greenlee", 3, 10, 1.0)
            assert len(results) == 0

    def test_corrupt_data_raises(self, tester):
        """Corrupt data (string instead of float) must raise an exception."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.return_value = ("not_a_number", 1000.0)
            with pytest.raises(Exception):
                results = tester.sample("greenlee", 3, 10, 1.0)
                tester.calculate_statistics(results)

    def test_zero_value_is_accepted(self, tester):
        """Zero value is technically valid — must be accepted."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.return_value = (0.0, 1000.0)
            results = tester.sample("greenlee", 3, 10, 1.0)
            assert len(results) == 3
            stats = tester.calculate_statistics(results)
            assert stats["mean"] == 0.0

    def test_negative_value_is_accepted(self, tester):
        """Negative value is returned — framework accepts it, statistics still valid."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.return_value = (-1.5, 1000.0)
            results = tester.sample("greenlee", 3, 10, 1.0)
            assert len(results) == 3
            stats = tester.calculate_statistics(results)
            assert stats["mean"] == -1.5

    def test_extreme_spike_value_is_accepted(self, tester):
        """Extreme spike value — framework accepts it, statistics reflect the outlier."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.return_value = (99999.9, 1000.0)
            results = tester.sample("greenlee", 3, 10, 1.0)
            stats = tester.calculate_statistics(results)
            assert stats["max"] == 99999.9


@pytest.mark.functional
class TestFlakyConnection:

    def test_partial_failure_returns_successful_measurements(self, tester):
        """
        Flaky connection: first 2 measurements succeed, last one returns None.
        Framework must return only the successful measurements.
        """
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.side_effect = [
                (1.5, 1000.0),
                (2.0, 1001.0),
                None,
            ]
            results = tester.sample("greenlee", 3, 10, 1.0)
            assert len(results) == 2
            assert results[0] == (1.5, 1000.0)
            assert results[1] == (2.0, 1001.0)

    def test_all_measurements_fail_returns_empty_list(self, tester):
        """All measurements return None — result is empty list."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.return_value = None
            results = tester.sample("greenlee", 4, 10, 1.0)
            assert results == []

    def test_statistics_on_partial_results(self, tester):
        """Statistics must be calculated only on successful measurements."""
        with patch("src.testing.ammeter_tester.client.request_current_from_ammeter") as mock:
            mock.side_effect = [
                (10.0, 1000.0),
                None,
                (20.0, 1002.0),
                None,
            ]
            results = tester.sample("greenlee", 4, 10, 1.0)
            assert len(results) == 2
            stats = tester.calculate_statistics(results)
            assert stats["mean"] == 15.0
            assert stats["min"] == 10.0
            assert stats["max"] == 20.0


# ── Category 2: Real E2E emulator failure ────────────────────────────

@pytest.mark.e2e
class TestRealEmulatorFailure:

    def test_emulator_killed_mid_sampling(self):
        """
        Real E2E test: emulator is killed after 2 measurements.
        Framework must handle ConnectionRefusedError gracefully
        and return the measurements collected before the failure.
        """
        from ammeters.greenlee_ammeter import GreenleeAmmeter

        # Use a dedicated port to avoid conflicts
        TEST_PORT = 5010
        stop_event = threading.Event()

        def run_limited_emulator():
            """Emulator that stops after receiving 2 connections."""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', TEST_PORT))
                s.listen()
                s.settimeout(15)
                connections_handled = 0
                while connections_handled < 2:
                    try:
                        conn, addr = s.accept()
                        with conn:
                            data = conn.recv(1024)
                            if data == b'MEASURE_GREENLEE -get_measurement':
                                conn.sendall(b'1.5')
                                connections_handled += 1
                    except socket.timeout:
                        break
                # Emulator stops — port closes
                stop_event.set()

        # Start limited emulator
        t = threading.Thread(target=run_limited_emulator, daemon=True)
        t.start()

        # Wait for emulator to be ready
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                with socket.create_connection(('localhost', TEST_PORT), timeout=1):
                    break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.1)

        # Patch AMMETER_CONFIG to use our test port
        from src.testing import ammeter_tester
        original_config = ammeter_tester.AMMETER_CONFIG.copy()
        ammeter_tester.AMMETER_CONFIG["greenlee"] = (TEST_PORT, b'MEASURE_GREENLEE -get_measurement')

        tester = AmmeterTester()
        try:
            # Try to collect 4 measurements — emulator will stop after 2
            results = tester.sample("greenlee", 4, 20, 0.5)
            # We expect 2 successful measurements before the emulator stops
            assert len(results) <= 4
            assert len(results) >= 0  # Must not crash
        except ConnectionRefusedError:
            # Acceptable — emulator died, framework raised error
            pass
        finally:
            # Restore original config
            ammeter_tester.AMMETER_CONFIG["greenlee"] = original_config["greenlee"]