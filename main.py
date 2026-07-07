import threading
import time

from ammeters                  import EMULATOR_CLASSES
from ammeters.client           import request_current_from_ammeter
from src.utils.config          import get_config

if __name__ == "__main__":
    cfg = get_config()

    # Start each ammeter in a separate thread
    for name, data in cfg["ammeters"].items():
        emulator = EMULATOR_CLASSES[name]
        port     = data["port"]
        threading.Thread(
            target=lambda e=emulator, p=port: e(p).start_server(),
            daemon=True
        ).start()

    # Wait for the servers to start
    time.sleep(5)

    # Request measurements from all ammeters
    for name, data in cfg["ammeters"].items():
        port    = data["port"]
        command = data["command"].encode()
        request_current_from_ammeter(port, command)
