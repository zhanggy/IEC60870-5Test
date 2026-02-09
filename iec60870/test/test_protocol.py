#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for IEC60870-5 protocol implementation
"""

import unittest
import struct
from iec60870.protocol import VSQ, IOA, CA
from iec60870.protocol.iec104 import APCI, ASDU
from iec60870.protocol.iec101 import FT12Frame


class TestVSQ(unittest.TestCase):
    """Test Variable Structure Qualifier"""
    
    def test_encode_decode(self):
        vsq = VSQ(sq=0, num=1)
        encoded = vsq.encode()
        self.assertEqual(encoded, 0x01)
        
        vsq2 = VSQ(sq=1, num=10)
        encoded2 = vsq2.encode()
        self.assertEqual(encoded2, 0x8A)
        
        decoded = VSQ.decode(0x01)
        self.assertEqual(decoded.sq, 0)
        self.assertEqual(decoded.num, 1)


class TestIOA(unittest.TestCase):
    """Test Information Object Address"""
    
    def test_encode_decode(self):
        ioa = IOA(0x123456)
        encoded = ioa.encode()
        self.assertEqual(encoded, [0x56, 0x34, 0x12])
        
        decoded = IOA.decode([0x56, 0x34, 0x12])
        self.assertEqual(decoded.address, 0x123456)


class TestCA(unittest.TestCase):
    """Test Common Address"""
    
    def test_encode_decode(self):
        ca = CA(0x1234)
        encoded = ca.encode()
        self.assertEqual(encoded, [0x34, 0x12])
        
        decoded = CA.decode([0x34, 0x12])
        self.assertEqual(decoded.address, 0x1234)


class TestAPCI(unittest.TestCase):
    """Test Application Protocol Control Information"""
    
    def test_i_format(self):
        # Test I-format encoding
        apci = APCI(0, send_seq=10, recv_seq=5)
        asdu_data = b'\x01\x02\x03'
        encoded = apci.encode(asdu_data)
        
        self.assertEqual(encoded[0], 0x68)  # Start byte
        self.assertEqual(encoded[1], 7)     # Length (4 + 3)
        
        # Test I-format decoding
        decoded_apci, decoded_asdu = APCI.decode(encoded)
        self.assertIsNotNone(decoded_apci)
        self.assertEqual(decoded_apci.type, 0)
        self.assertEqual(decoded_apci.send_seq, 10)
        self.assertEqual(decoded_apci.recv_seq, 5)
        self.assertEqual(decoded_asdu, b'\x01\x02\x03')
    
    def test_s_format(self):
        # Test S-format encoding
        apci = APCI(1, recv_seq=15)
        encoded = apci.encode()
        
        self.assertEqual(encoded[0], 0x68)  # Start byte
        self.assertEqual(encoded[1], 4)     # Length
        
        # Test S-format decoding
        decoded_apci, decoded_asdu = APCI.decode(encoded)
        self.assertIsNotNone(decoded_apci)
        self.assertEqual(decoded_apci.type, 1)
        self.assertIsNone(decoded_asdu)
    
    def test_u_format(self):
        # Test U-format encoding
        apci = APCI(2, recv_seq=0x04)
        encoded = apci.encode()
        
        self.assertEqual(encoded[0], 0x68)  # Start byte
        self.assertEqual(encoded[1], 4)     # Length
        
        # Test U-format decoding
        decoded_apci, decoded_asdu = APCI.decode(encoded)
        self.assertIsNotNone(decoded_apci)
        self.assertEqual(decoded_apci.type, 2)


class TestFT12Frame(unittest.TestCase):
    """Test FT1.2 Frame Format"""
    
    def test_fixed_frame(self):
        # Test fixed frame encoding
        frame = FT12Frame(control=0x40, address=1)
        encoded = frame.encode()
        
        self.assertEqual(encoded[0], 0x10)  # Start byte
        self.assertEqual(encoded[1], 0x40)  # Control
        self.assertEqual(encoded[2], 0x01)  # Address
        self.assertEqual(encoded[4], 0x16)  # End byte
        
        # Test fixed frame decoding
        decoded_frame, length = FT12Frame.decode(encoded)
        self.assertIsNotNone(decoded_frame)
        self.assertEqual(decoded_frame.control, 0x40)
        self.assertEqual(decoded_frame.address, 1)
        self.assertEqual(length, 5)
    
    def test_variable_frame(self):
        # Test variable frame encoding
        user_data = b'\x01\x02\x03\x04'
        frame = FT12Frame(control=0x43, address=1, data=user_data)
        encoded = frame.encode()
        
        self.assertEqual(encoded[0], 0x68)  # Start byte
        self.assertEqual(encoded[3], 0x68)  # Second start byte
        self.assertEqual(encoded[-1], 0x16)  # End byte
        
        # Test variable frame decoding
        decoded_frame, length = FT12Frame.decode(encoded)
        self.assertIsNotNone(decoded_frame)
        self.assertEqual(decoded_frame.control, 0x43)
        self.assertEqual(decoded_frame.address, 1)
        self.assertEqual(decoded_frame.data, user_data)


class TestASDU(unittest.TestCase):
    """Test Application Service Data Unit"""
    
    def test_encode_decode(self):
        vsq = VSQ(sq=0, num=1)
        ca = CA(1)
        ioa = IOA(100)
        data = b'\x14'  # QOI = 20
        
        asdu = ASDU(
            type_id=100,
            vsq=vsq,
            cot=6,
            ca=ca,
            ioa_list=[(ioa, data)]
        )
        
        encoded = asdu.encode()
        self.assertEqual(encoded[0], 100)  # Type ID
        self.assertEqual(encoded[2], 6)    # COT
        
        # Test decode
        decoded_asdu = ASDU.decode(encoded)
        self.assertIsNotNone(decoded_asdu)
        self.assertEqual(decoded_asdu.type_id, 100)
        self.assertEqual(decoded_asdu.cot, 6)
        self.assertEqual(decoded_asdu.ca.address, 1)
    
    def test_decode_malformed(self):
        """Test ASDU decode with malformed data"""
        # Too short data
        short_data = b'\x01\x02'
        asdu = ASDU.decode(short_data)
        self.assertIsNone(asdu)


if __name__ == '__main__':
    unittest.main()
