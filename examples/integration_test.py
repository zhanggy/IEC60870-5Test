#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration Test: IEC104 Client-Server Communication

This test demonstrates a complete client-server interaction.
"""

import time
import threading
import logging
from iec60870.protocol.iec104 import IEC104Client, IEC104Server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_client_server_communication():
    """Test basic client-server communication"""
    
    # Start server
    server = IEC104Server('127.0.0.1', 12404)
    if not server.start():
        logger.error("Failed to start server")
        return False
    
    time.sleep(1)  # Give server time to start
    
    # Create client
    client = IEC104Client('127.0.0.1', 12404)
    
    received_data = []
    
    def on_data(asdu):
        logger.info(f"Client received ASDU: Type={asdu.type_id}, COT={asdu.cot}")
        received_data.append(asdu)
    
    client.set_data_callback(on_data)
    
    # Connect client
    if not client.connect():
        logger.error("Failed to connect client")
        server.stop()
        return False
    
    try:
        # Wait for connection
        time.sleep(1)
        
        # Send STARTDT
        logger.info("Sending STARTDT...")
        client.send_startdt()
        time.sleep(1)
        
        # Send TESTFR
        logger.info("Sending TESTFR...")
        client.send_testfr()
        time.sleep(1)
        
        # Send interrogation
        logger.info("Sending interrogation...")
        client.send_interrogation(ca_address=1)
        time.sleep(2)
        
        # Send STOPDT
        logger.info("Sending STOPDT...")
        client.send_stopdt()
        time.sleep(1)
        
        success = True
        logger.info(f"Test completed successfully! Received {len(received_data)} ASDUs")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        success = False
    finally:
        client.disconnect()
        server.stop()
    
    return success


if __name__ == '__main__':
    logger.info("Starting IEC104 integration test...")
    success = test_client_server_communication()
    
    if success:
        logger.info("✓ Integration test PASSED")
        exit(0)
    else:
        logger.error("✗ Integration test FAILED")
        exit(1)
