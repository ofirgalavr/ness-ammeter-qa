# run_tests.py
# Simple runner to test all ammeters using the unified AmmeterTester interface.

import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from src.testing.AmmeterTester import AmmeterTester

def run_greenlee():
    GreenleeAmmeter(5000).start_server()

def run_entes():
    EntesAmmeter(5001).start_server()

def run_circutor():
    CircutorAmmeter(5002).start_server()
 
def start_emulators():
    # Start each ammeter server in a separate background thread
    threading.Thread(target=run_greenlee, daemon=True).start()
    threading.Thread(target=run_entes, daemon=True).start()
    threading.Thread(target=run_circutor, daemon=True).start()
    time.sleep(5)  # Wait for servers to start

if __name__ == "__main__":
    # Start emulators
    start_emulators()

    # Use AmmeterTester — sample, calculate statistics, and save results for each ammeter
    # Parameters: ammeter_type, num_measurements, duration (seconds), frequency (measurements per second)
    tester = AmmeterTester()

    print("\n--- Sampling Greenlee ---")
    greenlee_measurements = tester.sample("greenlee", num_measurements=4, duration=10, frequency=0.5)
    greenlee_stats = tester.calculate_statistics(greenlee_measurements)
    print(greenlee_measurements)
    print("Stats:", greenlee_stats)

    print("\n--- Sampling Entes ---")
    entes_measurements = tester.sample("entes", num_measurements=4, duration=10, frequency=0.5)
    entes_stats = tester.calculate_statistics(entes_measurements)
    print(entes_measurements)
    print("Stats:", entes_stats)

    print("\n--- Sampling Circutor ---")
    circutor_measurements = tester.sample("circutor", num_measurements=4, duration=10, frequency=0.5)
    circutor_stats = tester.calculate_statistics(circutor_measurements)
    print(circutor_measurements)
    print("Stats:", circutor_stats)

    # Save all results to a single file
    saved_path = tester.save_results({
        "greenlee": {"measurements": greenlee_measurements, "statistics": greenlee_stats},
        "entes":    {"measurements": entes_measurements,   "statistics": entes_stats},
        "circutor": {"measurements": circutor_measurements,"statistics": circutor_stats},
    })
    print("\nSaved to:", saved_path)

