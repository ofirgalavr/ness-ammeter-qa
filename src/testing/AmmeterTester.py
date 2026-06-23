# AmmeterTester.py
# Unified interface for communicating with all ammeter types.
# Hides port/command details from the caller — just pass the ammeter name.

from Ammeters import client


# Configuration: maps ammeter name -> (port, command)
AMMETER_CONFIG = {
    "greenlee": (5000, b'MEASURE_GREENLEE -get_measurement'),
    "entes":    (5001, b'MEASURE_ENTES -get_data'),
    "circutor": (5002, b'MEASURE_CIRCUTOR -get_measurement -current'),
}


class AmmeterTester:
    """
    Unified tester for all ammeter types.
    Knows which port and command belongs to each ammeter.
    """

    def measure(self, ammeter_type: str) -> None:
        """
        Send a measurement request to the specified ammeter.
        ammeter_type: "greenlee" / "entes" / "circutor"
        """
        # Look up port and command from the config dictionary
        if ammeter_type not in AMMETER_CONFIG:
            print(f"Unknown ammeter type: {ammeter_type}")
            return

        port, command = AMMETER_CONFIG[ammeter_type]
        client.request_current_from_ammeter(port, command)