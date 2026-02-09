#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: IEC104 Client Test

This example demonstrates how to use the IEC104 client to connect to a server,
send interrogation commands, and receive data.
"""

import logging
import time
from iec60870.protocol.iec104 import IEC104Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def data_callback(asdu):
    """Callback function for received ASDU data"""
    logger.info(f"Received ASDU:")
    logger.info(f"  Type ID: {asdu.type_id}")
    logger.info(f"  Cause of Transmission: {asdu.cot}")
    logger.info(f"  Common Address: {asdu.ca.address}")
    logger.info(f"  Number of objects: {len(asdu.ioa_list)}")
    
    for ioa, data in asdu.ioa_list:
        logger.info(f"    IOA: {ioa.address}, Data: {data.hex()}")


def main():
    # Configuration
    SERVER_HOST = '127.0.0.1'  # Change to your server address
    SERVER_PORT = 2404
    COMMON_ADDRESS = 1
    
    # Create client
    client = IEC104Client(SERVER_HOST, SERVER_PORT)
    client.set_data_callback(data_callback)
    
    # Connect to server
    logger.info(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")
    if not client.connect():
        logger.error("Failed to connect to server")
        return
    
    try:
        # Wait for connection to stabilize
        time.sleep(1)
        
        # Send STARTDT (Start Data Transfer)
        logger.info("Sending STARTDT...")
        client.send_startdt()
        time.sleep(1)
        
        # Send TESTFR (Test Frame)
        logger.info("Sending TESTFR...")
        client.send_testfr()
        time.sleep(1)
        
        # Send General Interrogation
        logger.info("Sending general interrogation...")
        client.send_interrogation(COMMON_ADDRESS)
        time.sleep(5)
        
        # Monitor for 30 seconds
        logger.info("Monitoring for 30 seconds...")
        time.sleep(30)
        
        # Send STOPDT (Stop Data Transfer)
        logger.info("Sending STOPDT...")
        client.send_stopdt()
        time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Disconnect
        client.disconnect()
        logger.info("Disconnected")


if __name__ == '__main__':
    main()
