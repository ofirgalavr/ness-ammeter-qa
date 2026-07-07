# run_tests.py
# Simple runner to test all ammeters using AmmeterTestFramework.

import threading
import time

from ammeters                   import EMULATOR_CLASSES
from src.testing.test_framework import AmmeterTestFramework
from src.utils.config           import get_config
from src.utils.visualizer       import plot_results

def start_emulators():
    # Use config singleton — no file I/O
    cfg = get_config()
    for name, data in cfg["ammeters"].items():
        port     = data["port"]
        emulator = EMULATOR_CLASSES[name]
        threading.Thread(target=lambda e=emulator, p=port: e(p).start_server(), daemon=True).start()
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
    results = {
        "greenlee": greenlee,
        "entes":    entes,
        "circutor": circutor,
    }
    saved_path = framework.tester.save_results(results)
    print("\nSaved to:", saved_path)

    # Generate visualization
    plot_results(results)
    print("Plot saved to: results/plots/")

    # Compare accuracy across ammeters
    accuracy = framework.tester.compare_accuracy(results)

    print("\n--- Accuracy Comparison ---")
    for ammeter, detail in accuracy["details"].items():
        print(f"  {ammeter:10} CV={detail['cv']:6.1f}%  ({detail['verdict']})")

    print(f"\n  Most consistent:  {accuracy['ranking'][0]}")
    print(f"  Least consistent: {accuracy['ranking'][-1]}")