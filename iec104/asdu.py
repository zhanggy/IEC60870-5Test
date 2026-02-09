"""
IEC60870-5-104协议ASDU (Application Service Data Unit) 实现
应用服务数据单元
"""

import struct


class InformationObject:
    """信息对象基类"""

    def __init__(self, ioa: int):
        self.ioa = ioa  # 信息对象地址

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码为字节序列"""
        raise NotImplementedError

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """从字节序列解码"""
        raise NotImplementedError


class SinglePointInformation(InformationObject):
    """单点信息 M_SP_NA_1 (TypeID=1)"""

    def __init__(self, ioa: int, value: bool, quality: int = 0):
        super().__init__(ioa)
        self.value = value
        self.quality = quality

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码"""
        ioa_bytes = self.ioa.to_bytes(ioa_size, 'little')
        siq = (self.quality & 0xFE) | (1 if self.value else 0)
        return ioa_bytes + bytes([siq])

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """解码"""
        ioa = int.from_bytes(data[:ioa_size], 'little')
        siq = data[ioa_size]
        value = bool(siq & 0x01)
        quality = siq & 0xFE
        return cls(ioa, value, quality)


class DoublePointInformation(InformationObject):
    """双点信息 M_DP_NA_1 (TypeID=3)"""

    def __init__(self, ioa: int, value: int, quality: int = 0):
        super().__init__(ioa)
        self.value = value  # 0=未确定, 1=分, 2=合, 3=未确定
        self.quality = quality

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码"""
        ioa_bytes = self.ioa.to_bytes(ioa_size, 'little')
        diq = (self.quality & 0xFC) | (self.value & 0x03)
        return ioa_bytes + bytes([diq])

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """解码"""
        ioa = int.from_bytes(data[:ioa_size], 'little')
        diq = data[ioa_size]
        value = diq & 0x03
        quality = diq & 0xFC
        return cls(ioa, value, quality)


class StepPositionInformation(InformationObject):
    """步位置信息 M_ST_NA_1 (TypeID=5)"""

    def __init__(self, ioa: int, value: int, transient: bool = False, quality: int = 0):
        super().__init__(ioa)
        self.value = value  # -64 到 +63
        self.transient = transient
        self.quality = quality

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码"""
        ioa_bytes = self.ioa.to_bytes(ioa_size, 'little')
        vti = (self.value & 0x7F) | (0x80 if self.transient else 0)
        qds = self.quality
        return ioa_bytes + bytes([vti, qds])

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """解码"""
        ioa = int.from_bytes(data[:ioa_size], 'little')
        vti = data[ioa_size]
        value = vti & 0x7F
        if value & 0x40:  # 符号扩展
            value = value - 128
        transient = bool(vti & 0x80)
        quality = data[ioa_size + 1]
        return cls(ioa, value, transient, quality)


class MeasuredValueNormalized(InformationObject):
    """测量值，归一化值 M_ME_NA_1 (TypeID=9)"""

    def __init__(self, ioa: int, value: float, quality: int = 0):
        super().__init__(ioa)
        self.value = value  # -1.0 到 +1.0
        self.quality = quality

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码"""
        ioa_bytes = self.ioa.to_bytes(ioa_size, 'little')
        # 归一化值范围 -1.0 到 +1.0 映射到 -32768 到 +32767
        nva = int(max(-32768, min(32767, self.value * 32767)))
        nva_bytes = struct.pack('<h', nva)
        qds = bytes([self.quality])
        return ioa_bytes + nva_bytes + qds

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """解码"""
        ioa = int.from_bytes(data[:ioa_size], 'little')
        nva = struct.unpack('<h', data[ioa_size:ioa_size + 2])[0]
        value = nva / 32767.0
        quality = data[ioa_size + 2]
        return cls(ioa, value, quality)


class MeasuredValueScaled(InformationObject):
    """测量值，标度化值 M_ME_NB_1 (TypeID=11)"""

    def __init__(self, ioa: int, value: int, quality: int = 0):
        super().__init__(ioa)
        self.value = value  # -32768 到 +32767
        self.quality = quality

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码"""
        ioa_bytes = self.ioa.to_bytes(ioa_size, 'little')
        sva_bytes = struct.pack('<h', self.value)
        qds = bytes([self.quality])
        return ioa_bytes + sva_bytes + qds

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """解码"""
        ioa = int.from_bytes(data[:ioa_size], 'little')
        sva = struct.unpack('<h', data[ioa_size:ioa_size + 2])[0]
        quality = data[ioa_size + 2]
        return cls(ioa, sva, quality)


class MeasuredValueFloat(InformationObject):
    """测量值，短浮点数 M_ME_NC_1 (TypeID=13)"""

    def __init__(self, ioa: int, value: float, quality: int = 0):
        super().__init__(ioa)
        self.value = value
        self.quality = quality

    def encode(self, ioa_size: int = 3) -> bytes:
        """编码"""
        ioa_bytes = self.ioa.to_bytes(ioa_size, 'little')
        ieee_bytes = struct.pack('<f', self.value)
        qds = bytes([self.quality])
        return ioa_bytes + ieee_bytes + qds

    @classmethod
    def decode(cls, data: bytes, ioa_size: int = 3):
        """解码"""
        ioa = int.from_bytes(data[:ioa_size], 'little')
        value = struct.unpack('<f', data[ioa_size:ioa_size + 4])[0]
        quality = data[ioa_size + 4]
        return cls(ioa, value, quality)


class ASDU:
    """应用服务数据单元"""

    def __init__(self, type_id: int, cot: int, oa: int, ca: int,
                 cot_size: int = 2, asdu_addr_size: int = 2, ioa_size: int = 3):
        self.type_id = type_id            # 类型标识
        self.vsq = 0                       # 可变结构限定词
        self.cot = cot                     # 传送原因
        self.oa = oa                       # 源发站地址
        self.ca = ca                       # 公共地址
        self.information_objects = []      # 信息对象列表

        # 配置参数
        self.cot_size = cot_size
        self.asdu_addr_size = asdu_addr_size
        self.ioa_size = ioa_size

    @property
    def num_objects(self) -> int:
        """信息对象数量"""
        return self.vsq & 0x7F

    @num_objects.setter
    def num_objects(self, value: int):
        """设置信息对象数量"""
        self.vsq = (self.vsq & 0x80) | (value & 0x7F)

    @property
    def is_sequence(self) -> bool:
        """是否为顺序"""
        return bool(self.vsq & 0x80)

    @is_sequence.setter
    def is_sequence(self, value: bool):
        """设置是否为顺序"""
        if value:
            self.vsq |= 0x80
        else:
            self.vsq &= 0x7F

    def add_information_object(self, obj: InformationObject):
        """添加信息对象"""
        self.information_objects.append(obj)
        self.num_objects = len(self.information_objects)

    def encode(self) -> bytes:
        """编码为字节序列"""
        # 类型标识
        data = bytes([self.type_id])

        # 可变结构限定词
        data += bytes([self.vsq])

        # 传送原因
        if self.cot_size == 1:
            data += bytes([self.cot & 0xFF])
        else:
            data += bytes([self.cot & 0xFF, self.oa & 0xFF])

        # 公共地址
        if self.asdu_addr_size == 1:
            data += bytes([self.ca & 0xFF])
        else:
            data += self.ca.to_bytes(self.asdu_addr_size, 'little')

        # 信息对象
        for obj in self.information_objects:
            data += obj.encode(self.ioa_size)

        return data

    @classmethod
    def decode(cls, data: bytes, cot_size: int = 2,
               asdu_addr_size: int = 2, ioa_size: int = 3) -> 'ASDU':
        """从字节序列解码"""
        offset = 0

        # 类型标识
        type_id = data[offset]
        offset += 1

        # 可变结构限定词
        vsq = data[offset]
        offset += 1

        # 传送原因
        cot = data[offset]
        offset += 1
        oa = 0
        if cot_size == 2:
            oa = data[offset]
            offset += 1

        # 公共地址
        ca = int.from_bytes(data[offset:offset + asdu_addr_size], 'little')
        offset += asdu_addr_size

        # 创建ASDU对象
        asdu = cls(type_id, cot, oa, ca, cot_size, asdu_addr_size, ioa_size)
        asdu.vsq = vsq

        # 解析信息对象（简化版本，需要根据type_id选择正确的解码类）
        # 这里仅作为框架示例

        return asdu

    def __str__(self) -> str:
        return f"ASDU(TypeID={self.type_id}, COT={self.cot}, CA={self.ca}, Objects={self.num_objects})"
