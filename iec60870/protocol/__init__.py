#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IEC60870-5 Protocol Common Definitions

This module contains common constants and data structures used in both
IEC60870-5-101 and IEC60870-5-104 protocols.
"""

# APCI (Application Protocol Control Information) Type Identifiers
APCI_TYPE_I = 0  # Information transfer format
APCI_TYPE_S = 1  # Supervisory functions
APCI_TYPE_U = 2  # Unnumbered control functions

# U-format control functions
U_STARTDT_ACT = 0x04   # Start data transfer activation
U_STARTDT_CON = 0x08   # Start data transfer confirmation
U_STOPDT_ACT = 0x10    # Stop data transfer activation
U_STOPDT_CON = 0x20    # Stop data transfer confirmation
U_TESTFR_ACT = 0x40    # Test frame activation
U_TESTFR_CON = 0x80    # Test frame confirmation

# Common ASDU Type Identifiers (TYP)
M_SP_NA_1 = 1   # Single-point information
M_SP_TA_1 = 2   # Single-point information with time tag
M_DP_NA_1 = 3   # Double-point information
M_DP_TA_1 = 4   # Double-point information with time tag
M_ST_NA_1 = 5   # Step position information
M_ST_TA_1 = 6   # Step position information with time tag
M_BO_NA_1 = 7   # Bitstring of 32 bit
M_BO_TA_1 = 8   # Bitstring of 32 bit with time tag
M_ME_NA_1 = 9   # Measured value, normalized value
M_ME_TA_1 = 10  # Measured value, normalized value with time tag
M_ME_NB_1 = 11  # Measured value, scaled value
M_ME_TB_1 = 12  # Measured value, scaled value with time tag
M_ME_NC_1 = 13  # Measured value, short floating point number
M_ME_TC_1 = 14  # Measured value, short floating point number with time tag
M_IT_NA_1 = 15  # Integrated totals
M_IT_TA_1 = 16  # Integrated totals with time tag

# Process commands
C_SC_NA_1 = 45  # Single command
C_DC_NA_1 = 46  # Double command
C_RC_NA_1 = 47  # Regulating step command
C_SE_NA_1 = 48  # Set point command, normalized value
C_SE_NB_1 = 49  # Set point command, scaled value
C_SE_NC_1 = 50  # Set point command, short floating point number

# System commands
C_IC_NA_1 = 100 # Interrogation command
C_CI_NA_1 = 101 # Counter interrogation command
C_RD_NA_1 = 102 # Read command
C_CS_NA_1 = 103 # Clock synchronization command
C_TS_NA_1 = 104 # Test command
C_RP_NA_1 = 105 # Reset process command

# Cause of Transmission (COT)
COT_PERIODIC = 1         # Periodic, cyclic
COT_BACKGROUND = 2       # Background scan
COT_SPONTANEOUS = 3      # Spontaneous
COT_INITIALIZED = 4      # Initialized
COT_REQUEST = 5          # Request or requested
COT_ACTIVATION = 6       # Activation
COT_ACTIVATION_CON = 7   # Activation confirmation
COT_DEACTIVATION = 8     # Deactivation
COT_DEACTIVATION_CON = 9 # Deactivation confirmation
COT_ACTIVATION_TERM = 10 # Activation termination
COT_INTERROGATED = 20    # Interrogated by station interrogation
COT_INTERROGATED_GROUP = 21  # Interrogated by group

# Variable Structure Qualifier (VSQ)
class VSQ:
    def __init__(self, sq=0, num=1):
        self.sq = sq    # Sequence bit
        self.num = num  # Number of information objects
    
    def encode(self):
        return ((self.sq & 0x01) << 7) | (self.num & 0x7F)
    
    @staticmethod
    def decode(byte):
        return VSQ(sq=(byte >> 7) & 0x01, num=byte & 0x7F)

# Information Object Address (IOA)
class IOA:
    def __init__(self, address):
        self.address = address
    
    def encode(self):
        """Encode to 3 bytes (little-endian)"""
        return [
            self.address & 0xFF,
            (self.address >> 8) & 0xFF,
            (self.address >> 16) & 0xFF
        ]
    
    @staticmethod
    def decode(bytes_data):
        """Decode from 3 bytes (little-endian)"""
        return IOA(bytes_data[0] | (bytes_data[1] << 8) | (bytes_data[2] << 16))

# Common Address of ASDU (CA)
class CA:
    def __init__(self, address):
        self.address = address
    
    def encode(self):
        """Encode to 2 bytes (little-endian)"""
        return [
            self.address & 0xFF,
            (self.address >> 8) & 0xFF
        ]
    
    @staticmethod
    def decode(bytes_data):
        """Decode from 2 bytes (little-endian)"""
        return CA(bytes_data[0] | (bytes_data[1] << 8))
