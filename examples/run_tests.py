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

    # Use AmmeterTester, unified interface
    tester = AmmeterTester()
    tester.measure("greenlee")
    tester.measure("entes")
    tester.measure("circutor")