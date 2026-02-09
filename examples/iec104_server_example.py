#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: IEC104 Server Test

This example demonstrates how to run a simple IEC104 server that responds to
client connections and commands.
"""

import logging
import time
from iec60870.protocol.iec104 import IEC104Server

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    # Configuration
    LISTEN_HOST = '0.0.0.0'  # Listen on all interfaces
    LISTEN_PORT = 2404
    
    # Create server
    server = IEC104Server(LISTEN_HOST, LISTEN_PORT)
    
    # Start server
    logger.info(f"Starting server on {LISTEN_HOST}:{LISTEN_PORT}...")
    if not server.start():
        logger.error("Failed to start server")
        return
    
    try:
        logger.info("Server is running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop server
        server.stop()
        logger.info("Server stopped")


if __name__ == '__main__':
    main()
