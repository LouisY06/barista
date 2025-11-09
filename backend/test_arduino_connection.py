#!/usr/bin/env python3
"""
Test script to connect to Arduino and send commands.
Run this after uploading the firmware via Arduino IDE.
"""

import serial
import serial.tools.list_ports
import time
import sys

def find_arduino_port():
    """Find Arduino port automatically."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'arduino' in port.description.lower() or 'usb' in port.description.lower():
            return port.device
    return None

def test_arduino_connection():
    """Test connection to Arduino."""
    print("=" * 60)
    print("Arduino Connection Test")
    print("=" * 60)
    
    # Find Arduino
    port = find_arduino_port()
    if port is None:
        print("\n❌ Arduino not found!")
        print("\nAvailable ports:")
        for p in serial.tools.list_ports.comports():
            print(f"  - {p.device}: {p.description}")
        return False
    
    print(f"\n✓ Found Arduino on: {port}")
    
    # Connect
    try:
        print("Connecting...")
        ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # Wait for Arduino to initialize
        
        # Read initial "READY" message
        if ser.in_waiting:
            response = ser.readline().decode('utf-8').strip()
            print(f"✓ Arduino says: {response}")
        
        # Test commands
        print("\n" + "=" * 60)
        print("Testing Commands:")
        print("=" * 60)
        
        commands = [
            ("STATUS", "Check status"),
            ("MOVE+", "Move motor forward"),
            ("STOP", "Stop motor"),
            ("MOVE-", "Move motor backward"),
            ("STOP", "Stop motor"),
        ]
        
        for cmd, description in commands:
            print(f"\n📤 Sending: {cmd} ({description})")
            ser.write(f"{cmd}\n".encode('utf-8'))
            time.sleep(0.5)
            
            if ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                print(f"📥 Response: {response}")
            else:
                print("   (No response)")
        
        # Test continuous mode
        print("\n" + "=" * 60)
        print("Testing Continuous Mode (TEST command):")
        print("=" * 60)
        print("📤 Sending: TEST")
        ser.write("TEST\n".encode('utf-8'))
        
        # Wait for test to complete
        print("   Waiting for test to complete...")
        time.sleep(5)
        
        if ser.in_waiting:
            response = ser.readline().decode('utf-8').strip()
            print(f"📥 Response: {response}")
        
        ser.close()
        print("\n✅ Test complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_arduino_connection()
    sys.exit(0 if success else 1)

