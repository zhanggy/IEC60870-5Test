"""
IEC60870-5-104协议APCI (Application Protocol Control Information) 实现
应用规约控制信息
"""

from typing import Optional
from .constants import APCIType, UType, ProtocolConstants


class APCI:
    """应用规约控制信息"""

    def __init__(self):
        self.start = ProtocolConstants.APCI_START_BYTE
        self.length = 4  # 默认长度（不包括起始字节和长度字节）
        self.control_field = bytearray(4)

    @property
    def format_type(self) -> int:
        """获取帧格式类型"""
        if (self.control_field[0] & 0x01) == 0:
            return APCIType.I_FORMAT
        elif (self.control_field[0] & 0x03) == 0x01:
            return APCIType.S_FORMAT
        else:
            return APCIType.U_FORMAT

    @property
    def send_seq(self) -> int:
        """获取发送序号(I格式)"""
        if self.format_type == APCIType.I_FORMAT:
            return ((self.control_field[1] << 7) | (self.control_field[0] >> 1)) & 0x7FFF
        return 0

    @send_seq.setter
    def send_seq(self, value: int):
        """设置发送序号(I格式)"""
        value = value & 0x7FFF
        self.control_field[0] = (value << 1) & 0xFE
        self.control_field[1] = (value >> 7) & 0xFF

    @property
    def recv_seq(self) -> int:
        """获取接收序号(I格式和S格式)"""
        if self.format_type == APCIType.I_FORMAT or self.format_type == APCIType.S_FORMAT:
            return ((self.control_field[3] << 7) | (self.control_field[2] >> 1)) & 0x7FFF
        return 0

    @recv_seq.setter
    def recv_seq(self, value: int):
        """设置接收序号(I格式和S格式)"""
        value = value & 0x7FFF
        self.control_field[2] = (value << 1) & 0xFE
        self.control_field[3] = (value >> 7) & 0xFF

    @property
    def utype(self) -> Optional[int]:
        """获取U格式功能码"""
        if self.format_type == APCIType.U_FORMAT:
            return self.control_field[0]
        return None

    @utype.setter
    def utype(self, value: int):
        """设置U格式功能码"""
        self.control_field[0] = value
        self.control_field[1] = 0
        self.control_field[2] = 0
        self.control_field[3] = 0

    def to_bytes(self) -> bytes:
        """转换为字节序列"""
        return bytes([self.start, self.length]) + bytes(self.control_field)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'APCI':
        """从字节序列解析"""
        if len(data) < ProtocolConstants.APCI_MIN_LENGTH:
            raise ValueError(f"APCI数据长度不足: {len(data)}")

        if data[0] != ProtocolConstants.APCI_START_BYTE:
            raise ValueError(f"APCI起始字节错误: 0x{data[0]:02X}")

        apci = cls()
        apci.length = data[1]
        apci.control_field = bytearray(data[2:6])
        return apci

    @classmethod
    def create_i_frame(cls, send_seq: int, recv_seq: int) -> 'APCI':
        """创建I格式帧"""
        apci = cls()
        apci.send_seq = send_seq
        apci.recv_seq = recv_seq
        return apci

    @classmethod
    def create_s_frame(cls, recv_seq: int) -> 'APCI':
        """创建S格式帧"""
        apci = cls()
        apci.control_field[0] = 0x01
        apci.control_field[1] = 0x00
        apci.recv_seq = recv_seq
        return apci

    @classmethod
    def create_u_frame(cls, utype: int) -> 'APCI':
        """创建U格式帧"""
        apci = cls()
        apci.utype = utype
        return apci

    def __str__(self) -> str:
        fmt_type = self.format_type
        if fmt_type == APCIType.I_FORMAT:
            return f"I-Frame(send={self.send_seq}, recv={self.recv_seq})"
        elif fmt_type == APCIType.S_FORMAT:
            return f"S-Frame(recv={self.recv_seq})"
        else:
            utype_names = {
                UType.STARTDT_ACT: "STARTDT_ACT",
                UType.STARTDT_CON: "STARTDT_CON",
                UType.STOPDT_ACT: "STOPDT_ACT",
                UType.STOPDT_CON: "STOPDT_CON",
                UType.TESTFR_ACT: "TESTFR_ACT",
                UType.TESTFR_CON: "TESTFR_CON"
            }
            utype_val = self.utype if self.utype is not None else 0
            return f"U-Frame({utype_names.get(utype_val, f'0x{utype_val:02X}')})"
