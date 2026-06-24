# run_tests.py
# Simple runner to test all ammeters using AmmeterTestFramework.

import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from src.testing.test_framework import AmmeterTestFramework

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
    start_emulators()

    framework = AmmeterTestFramework()

    print("\n--- Testing Greenlee ---")
    greenlee = framework.run_test("greenlee")
    print(greenlee["measurements"])
    print("Stats:", greenlee["statistics"])

    print("\n--- Testing Entes ---")
    entes = framework.run_test("entes")
    print(entes["measurements"])
    print("Stats:", entes["statistics"])

    print("\n--- Testing Circutor ---")
    circutor = framework.run_test("circutor")
    print(circutor["measurements"])
    print("Stats:", circutor["statistics"])

    # Save all results to a single file
    saved_path = framework.tester.save_results({
        "greenlee": greenlee,
        "entes":    entes,
        "circutor": circutor,
    })
    print("\nSaved to:", saved_path)