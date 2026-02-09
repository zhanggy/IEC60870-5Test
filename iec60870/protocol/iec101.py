#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IEC60870-5-101 Protocol Implementation

This module implements the IEC60870-5-101 protocol (Serial variant with FT1.2 frame format).
"""

import serial
import struct
import threading
import time
import logging
from typing import Optional, Callable

from . import (
    COT_ACTIVATION, COT_ACTIVATION_CON,
    VSQ, IOA, CA
)

logger = logging.getLogger(__name__)


class FT12Frame:
    """FT1.2 Frame Format for IEC60870-5-101"""
    
    START_BYTE_FIXED = 0x10
    START_BYTE_VARIABLE = 0x68
    END_BYTE = 0x16
    
    # Control field function codes
    FC_RESET_LINK = 0x00
    FC_RESET_USER_PROCESS = 0x01
    FC_USER_DATA = 0x03
    FC_ACK = 0x00
    FC_NACK = 0x01
    FC_STATUS_LINK = 0x09
    FC_STATUS_LINK_DATA = 0x0B
    
    def __init__(self, control, address, data=None):
        self.control = control
        self.address = address
        self.data = data if data else b''
    
    def encode(self):
        """Encode FT1.2 frame to bytes"""
        if len(self.data) == 0:
            # Fixed length frame
            frame = struct.pack('B', self.START_BYTE_FIXED)
            frame += struct.pack('B', self.control)
            frame += struct.pack('B', self.address)
            checksum = (self.control + self.address) & 0xFF
            frame += struct.pack('B', checksum)
            frame += struct.pack('B', self.END_BYTE)
            return frame
        else:
            # Variable length frame
            length = len(self.data) + 1  # +1 for control field
            frame = struct.pack('B', self.START_BYTE_VARIABLE)
            frame += struct.pack('B', length)
            frame += struct.pack('B', length)  # Repeated
            frame += struct.pack('B', self.START_BYTE_VARIABLE)
            frame += struct.pack('B', self.control)
            frame += struct.pack('B', self.address)
            frame += self.data
            
            # Calculate checksum
            checksum = self.control + self.address
            for byte in self.data:
                checksum += byte
            checksum &= 0xFF
            
            frame += struct.pack('B', checksum)
            frame += struct.pack('B', self.END_BYTE)
            return frame
    
    @staticmethod
    def decode(data):
        """Decode FT1.2 frame from bytes"""
        if len(data) < 5:
            return None
        
        start = data[0]
        
        if start == FT12Frame.START_BYTE_FIXED:
            # Fixed length frame (5 bytes)
            if len(data) < 5:
                return None
            
            control = data[1]
            address = data[2]
            checksum = data[3]
            end = data[4]
            
            if end != FT12Frame.END_BYTE:
                logger.error("Invalid end byte in fixed frame")
                return None
            
            calc_checksum = (control + address) & 0xFF
            if checksum != calc_checksum:
                logger.error("Checksum mismatch in fixed frame")
                return None
            
            return FT12Frame(control, address, None), 5
            
        elif start == FT12Frame.START_BYTE_VARIABLE:
            # Variable length frame
            if len(data) < 4:
                return None
            
            length1 = data[1]
            length2 = data[2]
            
            if length1 != length2:
                logger.error("Length mismatch in variable frame")
                return None
            
            frame_length = 6 + length1  # start(1) + len(1) + len(1) + start(1) + data + cs(1) + end(1)
            
            if len(data) < frame_length:
                return None
            
            if data[3] != FT12Frame.START_BYTE_VARIABLE:
                logger.error("Invalid second start byte")
                return None
            
            control = data[4]
            address = data[5]
            user_data = data[6:6+length1-1]
            checksum = data[6+length1-1]
            end = data[6+length1]
            
            if end != FT12Frame.END_BYTE:
                logger.error("Invalid end byte in variable frame")
                return None
            
            # Verify checksum
            calc_checksum = control + address
            for byte in user_data:
                calc_checksum += byte
            calc_checksum &= 0xFF
            
            if checksum != calc_checksum:
                logger.error("Checksum mismatch in variable frame")
                return None
            
            return FT12Frame(control, address, user_data), frame_length
        
        return None, 0


class IEC101Client:
    """IEC60870-5-101 Client Implementation"""
    
    def __init__(self, port, baudrate=9600, parity='E', stopbits=1, bytesize=8):
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.serial = None
        self.connected = False
        self.recv_thread = None
        self.running = False
        self.on_data_callback = None
        self.link_address = 1  # Default link address
    
    def connect(self):
        """Connect to serial port"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=1
            )
            self.connected = True
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            
            # Start receive thread
            self.running = True
            self.recv_thread = threading.Thread(target=self._receive_loop)
            self.recv_thread.daemon = True
            self.recv_thread.start()
            
            # Send reset link
            self.send_reset_link()
            time.sleep(0.1)
            
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        self.running = False
        if self.serial:
            try:
                self.serial.close()
            except:
                pass
        self.connected = False
        logger.info("Disconnected")
    
    def send_reset_link(self):
        """Send reset link command"""
        control = 0x40 | FT12Frame.FC_RESET_LINK  # DIR=0, PRM=1, FC=0
        frame = FT12Frame(control, self.link_address)
        data = frame.encode()
        self.serial.write(data)
        logger.info("Sent RESET LINK")
    
    def send_user_data(self, asdu_data):
        """Send user data"""
        control = 0x43  # DIR=0, PRM=1, FC=3 (User data)
        frame = FT12Frame(control, self.link_address, asdu_data)
        data = frame.encode()
        self.serial.write(data)
        logger.info("Sent USER DATA")
    
    def send_interrogation(self, ca_address=1):
        """Send general interrogation command"""
        # Build ASDU for interrogation
        asdu = bytearray()
        asdu.append(100)  # Type ID: C_IC_NA_1
        asdu.append(0x01)  # VSQ: SQ=0, NUM=1
        asdu.append(COT_ACTIVATION)  # COT
        asdu.append(0)  # Originator address
        asdu.append(ca_address & 0xFF)  # CA low byte
        asdu.append((ca_address >> 8) & 0xFF)  # CA high byte
        
        # Information object
        asdu.append(0)  # IOA byte 1
        asdu.append(0)  # IOA byte 2
        asdu.append(0)  # IOA byte 3
        asdu.append(20)  # QOI = 20 (station interrogation)
        
        self.send_user_data(bytes(asdu))
        logger.info("Sent interrogation command")
    
    def _receive_loop(self):
        """Receive loop for incoming data"""
        buffer = b''
        
        while self.running:
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    buffer += data
                    
                    # Try to parse frames
                    while len(buffer) >= 5:
                        result = FT12Frame.decode(buffer)
                        if result is None:
                            # Invalid frame, skip first byte
                            buffer = buffer[1:]
                            continue
                        
                        frame, length = result
                        if frame is None:
                            break  # Need more data
                        
                        buffer = buffer[length:]
                        self._process_frame(frame)
                else:
                    time.sleep(0.01)
                    
            except Exception as e:
                if self.running:
                    logger.error(f"Receive error: {e}")
                break
    
    def _process_frame(self, frame):
        """Process received frame"""
        logger.info(f"Received frame: control=0x{frame.control:02X}, address={frame.address}")
        
        # Check if it's user data
        fc = frame.control & 0x0F
        if fc == FT12Frame.FC_USER_DATA and frame.data:
            # Parse ASDU
            if self.on_data_callback:
                self.on_data_callback(frame.data)
    
    def set_data_callback(self, callback):
        """Set callback for received data"""
        self.on_data_callback = callback
