#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: IEC101 Client Test

This example demonstrates how to use the IEC101 client to communicate over serial port.
Note: You need a serial port or virtual serial port for this example.
"""

import logging
import time
from iec60870.protocol.iec101 import IEC101Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def data_callback(data):
    """Callback function for received data"""
    logger.info(f"Received data: {data.hex()}")


def main():
    # Configuration
    # On Linux: '/dev/ttyUSB0' or '/dev/ttyS0'
    # On Windows: 'COM1', 'COM2', etc.
    SERIAL_PORT = '/dev/ttyUSB0'
    BAUDRATE = 9600
    COMMON_ADDRESS = 1
    
    # Create client
    client = IEC101Client(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        parity='E',  # Even parity
        stopbits=1
    )
    client.set_data_callback(data_callback)
    
    # Connect to serial port
    logger.info(f"Connecting to {SERIAL_PORT} at {BAUDRATE} baud...")
    if not client.connect():
        logger.error("Failed to connect to serial port")
        logger.info("Make sure the serial port exists and you have permissions")
        return
    
    try:
        # Wait for connection to stabilize
        time.sleep(2)
        
        # Send General Interrogation
        logger.info("Sending general interrogation...")
        client.send_interrogation(COMMON_ADDRESS)
        time.sleep(5)
        
        # Monitor for 30 seconds
        logger.info("Monitoring for 30 seconds...")
        time.sleep(30)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Disconnect
        client.disconnect()
        logger.info("Disconnected")


if __name__ == '__main__':
    main()
