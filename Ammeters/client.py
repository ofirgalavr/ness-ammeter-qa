from socket import socket, AF_INET, SOCK_STREAM
import time


def request_current_from_ammeter(port: int, command: bytes) -> tuple[float, float]:
    """
    Send a command to the ammeter and return the measurement result.
    Returns a tuple: (current_value: float, timestamp: float)
    timestamp is seconds since epoch (time.time())
    Raises ValueError if no data is received — Fail Fast, never returns None.
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(('localhost', port))
        s.sendall(command)
        data = s.recv(1024)
        if not data:
            raise ValueError(f"No data received from ammeter on port {port}")
        value = float(data.decode('utf-8'))
        timestamp = time.time()
        print(f"Received current measurement from port {port}: {value} A")
        return (value, timestamp)