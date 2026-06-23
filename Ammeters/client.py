from socket import socket, AF_INET, SOCK_STREAM
import time


def request_current_from_ammeter(port: int, command: bytes):
    """
    Send a command to the ammeter and return the measurement result.
    Returns a tuple: (current_value: float, timestamp: float)
    timestamp is seconds since epoch (time.time())
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(('localhost', port))
        s.sendall(command)
        data = s.recv(1024)
        if data:
            value = float(data.decode('utf-8'))
            timestamp = time.time()
            print(f"Received current measurement from port {port}: {value} A")
            return (value, timestamp)
        else:
            print("No data received.")
            return None