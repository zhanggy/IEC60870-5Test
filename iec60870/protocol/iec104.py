#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IEC60870-5-104 Protocol Implementation

This module implements the IEC60870-5-104 protocol (TCP/IP variant).
"""

import socket
import struct
import threading
import time
import logging
from typing import Optional, Callable, List

from . import (
    APCI_TYPE_I, APCI_TYPE_S, APCI_TYPE_U,
    U_STARTDT_ACT, U_STARTDT_CON, U_STOPDT_ACT, U_STOPDT_CON,
    U_TESTFR_ACT, U_TESTFR_CON,
    COT_ACTIVATION, COT_ACTIVATION_CON,
    VSQ, IOA, CA
)

logger = logging.getLogger(__name__)


class APCI:
    """Application Protocol Control Information"""
    START_BYTE = 0x68
    
    def __init__(self, apci_type, send_seq=0, recv_seq=0):
        self.type = apci_type
        self.send_seq = send_seq  # Only for I-format
        self.recv_seq = recv_seq  # For I-format and S-format
    
    def encode(self, asdu_data=None):
        """Encode APCI to bytes"""
        if self.type == APCI_TYPE_I:
            # I-format: Information transfer
            length = 4 + (len(asdu_data) if asdu_data else 0)
            apci = struct.pack('B', self.START_BYTE)
            apci += struct.pack('B', length)
            apci += struct.pack('<H', (self.send_seq << 1) & 0xFFFE)
            apci += struct.pack('<H', (self.recv_seq << 1) & 0xFFFE)
            if asdu_data:
                apci += asdu_data
            return apci
        elif self.type == APCI_TYPE_S:
            # S-format: Supervisory
            apci = struct.pack('B', self.START_BYTE)
            apci += struct.pack('B', 4)  # Length is always 4 for S-format
            apci += struct.pack('<H', 0x0001)  # S-format identifier
            apci += struct.pack('<H', (self.recv_seq << 1) & 0xFFFE)
            return apci
        elif self.type == APCI_TYPE_U:
            # U-format: Unnumbered control
            apci = struct.pack('B', self.START_BYTE)
            apci += struct.pack('B', 4)  # Length is always 4 for U-format
            # Set bits 0-1 to indicate U-format (0x03) and include control function
            apci += struct.pack('<H', self.recv_seq | 0x03)  # U-format control field
            apci += struct.pack('<H', 0x0000)
            return apci
    
    @staticmethod
    def decode(data):
        """Decode APCI from bytes"""
        if len(data) < 2:
            return None, None
        
        start = data[0]
        if start != APCI.START_BYTE:
            logger.error(f"Invalid start byte: 0x{start:02X}")
            return None, None
        
        length = data[1]
        if len(data) < length + 2:
            return None, None
        
        control1 = struct.unpack('<H', data[2:4])[0]
        control2 = struct.unpack('<H', data[4:6])[0]
        
        # Determine APCI type
        # Check U-format first (both bits set)
        if (control1 & 0x03) == 0x03:
            # U-format
            apci = APCI(APCI_TYPE_U, recv_seq=control1)
            return apci, None
        elif (control1 & 0x01) == 0:
            # I-format (bit 0 = 0)
            send_seq = (control1 >> 1) & 0x7FFF
            recv_seq = (control2 >> 1) & 0x7FFF
            apci = APCI(APCI_TYPE_I, send_seq, recv_seq)
            asdu_data = data[6:length+2]
            return apci, asdu_data
        elif (control1 & 0x03) == 0x01:
            # S-format (bit 0 = 1, bit 1 = 0)
            recv_seq = (control2 >> 1) & 0x7FFF
            apci = APCI(APCI_TYPE_S, recv_seq=recv_seq)
            return apci, None
        
        return None, None


class ASDU:
    """Application Service Data Unit"""
    
    def __init__(self, type_id, vsq, cot, ca, ioa_list):
        self.type_id = type_id  # Type Identification
        self.vsq = vsq          # Variable Structure Qualifier
        self.cot = cot          # Cause of Transmission
        self.ca = ca            # Common Address
        self.ioa_list = ioa_list  # List of (IOA, data)
    
    def encode(self):
        """Encode ASDU to bytes"""
        asdu = struct.pack('B', self.type_id)
        asdu += struct.pack('B', self.vsq.encode())
        asdu += struct.pack('B', self.cot)
        asdu += struct.pack('B', 0)  # Originator address (usually 0)
        asdu += bytes(self.ca.encode())
        
        for ioa, data in self.ioa_list:
            asdu += bytes(ioa.encode())
            asdu += data
        
        return asdu
    
    @staticmethod
    def decode(data):
        """Decode ASDU from bytes"""
        if len(data) < 6:
            return None
        
        type_id = data[0]
        vsq = VSQ.decode(data[1])
        cot = data[2]
        # data[3] is originator address
        ca = CA.decode(data[4:6])
        
        # Parse information objects
        ioa_list = []
        offset = 6
        
        for i in range(vsq.num):
            if offset + 3 > len(data):
                break
            
            if vsq.sq == 0:
                # Each object has its own address
                ioa = IOA.decode(data[offset:offset+3])
                offset += 3
            else:
                # Sequential: only first object has address
                if i == 0:
                    ioa = IOA.decode(data[offset:offset+3])
                    offset += 3
                else:
                    ioa = IOA(ioa.address + 1)
            
            # Parse information element based on type_id
            # For now, just capture remaining data
            remaining = len(data) - offset
            if remaining > 0:
                # Simplified: take all remaining data as the element
                element_data = data[offset:]
                ioa_list.append((ioa, element_data))
                break
        
        return ASDU(type_id, vsq, cot, ca, ioa_list)


class IEC104Client:
    """IEC60870-5-104 Client Implementation"""
    
    def __init__(self, host, port=2404):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.send_seq = 0
        self.recv_seq = 0
        self.recv_thread = None
        self.running = False
        self.on_data_callback = None
    
    def connect(self):
        """Connect to IEC104 server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to {self.host}:{self.port}")
            
            # Start receive thread
            self.running = True
            self.recv_thread = threading.Thread(target=self._receive_loop)
            self.recv_thread.daemon = True
            self.recv_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IEC104 server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        logger.info("Disconnected")
    
    def send_startdt(self):
        """Send STARTDT (Start Data Transfer) command"""
        apci = APCI(APCI_TYPE_U, recv_seq=U_STARTDT_ACT)
        data = apci.encode()
        self.socket.sendall(data)
        logger.info("Sent STARTDT ACT")
    
    def send_stopdt(self):
        """Send STOPDT (Stop Data Transfer) command"""
        apci = APCI(APCI_TYPE_U, recv_seq=U_STOPDT_ACT)
        data = apci.encode()
        self.socket.sendall(data)
        logger.info("Sent STOPDT ACT")
    
    def send_testfr(self):
        """Send TESTFR (Test Frame) command"""
        apci = APCI(APCI_TYPE_U, recv_seq=U_TESTFR_ACT)
        data = apci.encode()
        self.socket.sendall(data)
        logger.info("Sent TESTFR ACT")
    
    def send_asdu(self, asdu):
        """Send ASDU (Application Service Data Unit)"""
        asdu_data = asdu.encode()
        apci = APCI(APCI_TYPE_I, self.send_seq, self.recv_seq)
        data = apci.encode(asdu_data)
        self.socket.sendall(data)
        self.send_seq = (self.send_seq + 1) & 0x7FFF
        logger.info(f"Sent I-frame (seq={self.send_seq})")
    
    def send_interrogation(self, ca_address=1):
        """Send general interrogation command"""
        vsq = VSQ(sq=0, num=1)
        ca = CA(ca_address)
        ioa = IOA(0)  # Qualifier of interrogation
        data = bytes([20])  # QOI = 20 (station interrogation)
        
        asdu = ASDU(
            type_id=100,  # C_IC_NA_1
            vsq=vsq,
            cot=COT_ACTIVATION,
            ca=ca,
            ioa_list=[(ioa, data)]
        )
        self.send_asdu(asdu)
        logger.info("Sent interrogation command")
    
    def _receive_loop(self):
        """Receive loop for incoming data"""
        buffer = b''
        
        while self.running:
            try:
                data = self.socket.recv(1024)
                if not data:
                    logger.warning("Connection closed by server")
                    self.connected = False
                    break
                
                buffer += data
                
                # Process complete APDUs
                while len(buffer) >= 2:
                    if buffer[0] != APCI.START_BYTE:
                        logger.error("Invalid start byte, skipping")
                        buffer = buffer[1:]
                        continue
                    
                    length = buffer[1]
                    apdu_length = length + 2
                    
                    if len(buffer) < apdu_length:
                        break  # Wait for more data
                    
                    apdu_data = buffer[:apdu_length]
                    buffer = buffer[apdu_length:]
                    
                    self._process_apdu(apdu_data)
                    
            except Exception as e:
                if self.running:
                    logger.error(f"Receive error: {e}")
                break
    
    def _process_apdu(self, data):
        """Process received APDU"""
        apci, asdu_data = APCI.decode(data)
        
        if apci is None:
            logger.error("Failed to decode APCI")
            return
        
        if apci.type == APCI_TYPE_I:
            # I-format: Information transfer
            self.recv_seq = (apci.send_seq + 1) & 0x7FFF
            logger.info(f"Received I-frame (seq={apci.send_seq})")
            
            if asdu_data:
                asdu = ASDU.decode(asdu_data)
                if asdu and self.on_data_callback:
                    self.on_data_callback(asdu)
                    
        elif apci.type == APCI_TYPE_S:
            # S-format: Supervisory
            logger.info(f"Received S-frame (recv_seq={apci.recv_seq})")
            
        elif apci.type == APCI_TYPE_U:
            # U-format: Unnumbered control
            if apci.recv_seq == U_STARTDT_CON:
                logger.info("Received STARTDT CON")
            elif apci.recv_seq == U_STOPDT_CON:
                logger.info("Received STOPDT CON")
            elif apci.recv_seq == U_TESTFR_CON:
                logger.info("Received TESTFR CON")
            elif apci.recv_seq == U_TESTFR_ACT:
                logger.info("Received TESTFR ACT")
                # Send TESTFR CON
                resp = APCI(APCI_TYPE_U, recv_seq=U_TESTFR_CON)
                self.socket.sendall(resp.encode())
    
    def set_data_callback(self, callback):
        """Set callback for received ASDU data"""
        self.on_data_callback = callback


class IEC104Server:
    """IEC60870-5-104 Server Implementation"""
    
    def __init__(self, host='0.0.0.0', port=2404):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.accept_thread = None
    
    def start(self):
        """Start IEC104 server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"Server listening on {self.host}:{self.port}")
            
            # Start accept thread
            self.accept_thread = threading.Thread(target=self._accept_loop)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop IEC104 server"""
        self.running = False
        for client in self.clients:
            client['socket'].close()
        if self.server_socket:
            self.server_socket.close()
        logger.info("Server stopped")
    
    def _accept_loop(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"Client connected from {address}")
                
                client = {
                    'socket': client_socket,
                    'address': address,
                    'send_seq': 0,
                    'recv_seq': 0
                }
                self.clients.append(client)
                
                # Start client handler thread
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client,)
                )
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {e}")
    
    def _handle_client(self, client):
        """Handle client connection"""
        client_socket = client['socket']
        buffer = b''
        
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    logger.info(f"Client {client['address']} disconnected")
                    break
                
                buffer += data
                
                # Process complete APDUs
                while len(buffer) >= 2:
                    if buffer[0] != APCI.START_BYTE:
                        buffer = buffer[1:]
                        continue
                    
                    length = buffer[1]
                    apdu_length = length + 2
                    
                    if len(buffer) < apdu_length:
                        break
                    
                    apdu_data = buffer[:apdu_length]
                    buffer = buffer[apdu_length:]
                    
                    self._process_client_apdu(client, apdu_data)
                    
            except Exception as e:
                logger.error(f"Client handler error: {e}")
                break
        
        # Remove client
        if client in self.clients:
            self.clients.remove(client)
        client_socket.close()
    
    def _process_client_apdu(self, client, data):
        """Process APDU from client"""
        apci, asdu_data = APCI.decode(data)
        
        if apci is None:
            return
        
        if apci.type == APCI_TYPE_U:
            # Handle U-format commands
            if apci.recv_seq == U_STARTDT_ACT:
                logger.info("Received STARTDT ACT")
                # Send STARTDT CON
                resp = APCI(APCI_TYPE_U, recv_seq=U_STARTDT_CON)
                client['socket'].sendall(resp.encode())
            elif apci.recv_seq == U_STOPDT_ACT:
                logger.info("Received STOPDT ACT")
                # Send STOPDT CON
                resp = APCI(APCI_TYPE_U, recv_seq=U_STOPDT_CON)
                client['socket'].sendall(resp.encode())
            elif apci.recv_seq == U_TESTFR_ACT:
                logger.info("Received TESTFR ACT")
                # Send TESTFR CON
                resp = APCI(APCI_TYPE_U, recv_seq=U_TESTFR_CON)
                client['socket'].sendall(resp.encode())
        
        elif apci.type == APCI_TYPE_I:
            # I-format: Information transfer
            client['recv_seq'] = (apci.send_seq + 1) & 0x7FFF
            logger.info(f"Received I-frame from client")
            
            if asdu_data:
                asdu = ASDU.decode(asdu_data)
                if asdu:
                    # Handle ASDU (e.g., interrogation, commands)
                    self._handle_asdu(client, asdu)
    
    def _handle_asdu(self, client, asdu):
        """Handle received ASDU"""
        logger.info(f"Received ASDU type={asdu.type_id}, COT={asdu.cot}")
        
        # Example: respond to interrogation command
        if asdu.type_id == 100:  # C_IC_NA_1
            logger.info("Processing interrogation command")
            # Send interrogation confirmation
            vsq = VSQ(sq=0, num=1)
            ioa = IOA(0)
            data = bytes([20])  # QOI = 20
            
            resp_asdu = ASDU(
                type_id=100,
                vsq=vsq,
                cot=COT_ACTIVATION_CON,
                ca=asdu.ca,
                ioa_list=[(ioa, data)]
            )
            
            # Send response
            asdu_data = resp_asdu.encode()
            apci = APCI(APCI_TYPE_I, client['send_seq'], client['recv_seq'])
            resp_data = apci.encode(asdu_data)
            client['socket'].sendall(resp_data)
            client['send_seq'] = (client['send_seq'] + 1) & 0x7FFF
