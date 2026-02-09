#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IEC60870-5-101/104 Test Tool - Command Line Interface

This module provides the command-line interface for testing IEC60870-5 protocols.
"""

import argparse
import logging
import sys
import time
from datetime import datetime

from iec60870.protocol.iec104 import IEC104Client, IEC104Server
from iec60870.protocol.iec101 import IEC101Client


def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_iec104_client(args):
    """Run IEC104 client test"""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting IEC104 Client")
    logger.info(f"Target: {args.host}:{args.port}")
    
    client = IEC104Client(args.host, args.port)
    
    def on_data(asdu):
        logger.info(f"Received ASDU: Type={asdu.type_id}, COT={asdu.cot}, CA={asdu.ca.address}")
        logger.info(f"  Number of objects: {len(asdu.ioa_list)}")
        for ioa, data in asdu.ioa_list:
            logger.info(f"  IOA={ioa.address}, Data={data.hex()}")
    
    client.set_data_callback(on_data)
    
    if not client.connect():
        logger.error("Failed to connect")
        return 1
    
    try:
        # Wait for connection to stabilize
        time.sleep(1)
        
        # Send STARTDT
        client.send_startdt()
        time.sleep(1)
        
        # Send test frame
        if args.testfr:
            logger.info("Sending test frame...")
            client.send_testfr()
            time.sleep(1)
        
        # Send interrogation
        if args.interrogation:
            logger.info("Sending general interrogation...")
            client.send_interrogation(args.ca)
            time.sleep(2)
        
        # Keep connection alive
        logger.info(f"Monitoring for {args.duration} seconds...")
        for i in range(args.duration):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                logger.info(f"Running... {i}/{args.duration} seconds")
        
        # Send STOPDT
        client.send_stopdt()
        time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        client.disconnect()
    
    return 0


def run_iec104_server(args):
    """Run IEC104 server test"""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting IEC104 Server")
    logger.info(f"Listening on {args.host}:{args.port}")
    
    server = IEC104Server(args.host, args.port)
    
    if not server.start():
        logger.error("Failed to start server")
        return 1
    
    try:
        logger.info("Server running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        server.stop()
    
    return 0


def run_iec101_client(args):
    """Run IEC101 client test"""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting IEC101 Client")
    logger.info(f"Serial port: {args.port}")
    logger.info(f"Baudrate: {args.baudrate}")
    
    client = IEC101Client(
        port=args.port,
        baudrate=args.baudrate,
        parity=args.parity,
        stopbits=args.stopbits
    )
    
    def on_data(data):
        logger.info(f"Received data: {data.hex()}")
    
    client.set_data_callback(on_data)
    
    if not client.connect():
        logger.error("Failed to connect")
        return 1
    
    try:
        # Wait for connection to stabilize
        time.sleep(1)
        
        # Send interrogation
        if args.interrogation:
            logger.info("Sending general interrogation...")
            client.send_interrogation(args.ca)
            time.sleep(2)
        
        # Keep connection alive
        logger.info(f"Monitoring for {args.duration} seconds...")
        for i in range(args.duration):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                logger.info(f"Running... {i}/{args.duration} seconds")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        client.disconnect()
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='IEC60870-5-101/104 Protocol Test Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run IEC104 client and send interrogation
  %(prog)s iec104-client --host 192.168.1.100 --interrogation
  
  # Run IEC104 server
  %(prog)s iec104-server --host 0.0.0.0 --port 2404
  
  # Run IEC101 client
  %(prog)s iec101-client --port /dev/ttyUSB0 --baudrate 9600 --interrogation
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # IEC104 Client
    iec104_client = subparsers.add_parser(
        'iec104-client',
        help='Run IEC104 client'
    )
    iec104_client.add_argument(
        '--host',
        required=True,
        help='Server host address'
    )
    iec104_client.add_argument(
        '--port',
        type=int,
        default=2404,
        help='Server port (default: 2404)'
    )
    iec104_client.add_argument(
        '--ca',
        type=int,
        default=1,
        help='Common address (default: 1)'
    )
    iec104_client.add_argument(
        '--interrogation',
        action='store_true',
        help='Send general interrogation command'
    )
    iec104_client.add_argument(
        '--testfr',
        action='store_true',
        help='Send test frame'
    )
    iec104_client.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Monitoring duration in seconds (default: 30)'
    )
    
    # IEC104 Server
    iec104_server = subparsers.add_parser(
        'iec104-server',
        help='Run IEC104 server'
    )
    iec104_server.add_argument(
        '--host',
        default='0.0.0.0',
        help='Listen address (default: 0.0.0.0)'
    )
    iec104_server.add_argument(
        '--port',
        type=int,
        default=2404,
        help='Listen port (default: 2404)'
    )
    
    # IEC101 Client
    iec101_client = subparsers.add_parser(
        'iec101-client',
        help='Run IEC101 client'
    )
    iec101_client.add_argument(
        '--port',
        required=True,
        help='Serial port (e.g., /dev/ttyUSB0 or COM1)'
    )
    iec101_client.add_argument(
        '--baudrate',
        type=int,
        default=9600,
        help='Baudrate (default: 9600)'
    )
    iec101_client.add_argument(
        '--parity',
        choices=['N', 'E', 'O'],
        default='E',
        help='Parity: N=None, E=Even, O=Odd (default: E)'
    )
    iec101_client.add_argument(
        '--stopbits',
        type=int,
        choices=[1, 2],
        default=1,
        help='Stop bits (default: 1)'
    )
    iec101_client.add_argument(
        '--ca',
        type=int,
        default=1,
        help='Common address (default: 1)'
    )
    iec101_client.add_argument(
        '--interrogation',
        action='store_true',
        help='Send general interrogation command'
    )
    iec101_client.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Monitoring duration in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'iec104-client':
        return run_iec104_client(args)
    elif args.command == 'iec104-server':
        return run_iec104_server(args)
    elif args.command == 'iec101-client':
        return run_iec101_client(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
