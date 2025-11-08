"""
Serial communication handler for Arduino communication.

This module can be extended for more advanced serial communication handling,
including async message processing and status monitoring.
"""

import serial
import threading
import queue
from typing import Optional, Callable


class SerialHandler:
    """Handles serial communication with Arduino."""
    
    def __init__(self, port: str, baud_rate: int = 9600):
        self.port = port
        self.baud_rate = baud_rate
        self.connection: Optional[serial.Serial] = None
        self.message_queue = queue.Queue()
        self.running = False
        self.read_thread: Optional[threading.Thread] = None
        self.callbacks: list[Callable[[str], None]] = []
    
    def connect(self) -> bool:
        """Connect to Arduino."""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1
            )
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            return True
        except Exception as e:
            print(f"Error connecting: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino."""
        self.running = False
        if self.connection and self.connection.is_open:
            self.connection.close()
    
    def send(self, message: str) -> bool:
        """Send message to Arduino."""
        if not self.connection or not self.connection.is_open:
            return False
        try:
            self.connection.write(f"{message}\n".encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def _read_loop(self):
        """Background thread to continuously read from serial."""
        while self.running:
            if self.connection and self.connection.in_waiting:
                try:
                    message = self.connection.readline().decode('utf-8').strip()
                    self.message_queue.put(message)
                    # Notify callbacks
                    for callback in self.callbacks:
                        callback(message)
                except Exception as e:
                    print(f"Error reading message: {e}")
    
    def register_callback(self, callback: Callable[[str], None]):
        """Register a callback for incoming messages."""
        self.callbacks.append(callback)
    
    def get_message(self, timeout: Optional[float] = None) -> Optional[str]:
        """Get a message from the queue."""
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

