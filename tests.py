"""
IEC60870-5-104协议单元测试
"""

import unittest
from iec104 import (
    APCI, ASDU, APCIType, UType, TypeID, COT,
    SinglePointInformation, DoublePointInformation,
    MeasuredValueNormalized, MeasuredValueScaled, MeasuredValueFloat
)


class TestAPCI(unittest.TestCase):
    """APCI测试"""

    def test_create_i_frame(self):
        """测试创建I格式帧"""
        apci = APCI.create_i_frame(100, 200)
        self.assertEqual(apci.format_type, APCIType.I_FORMAT)
        self.assertEqual(apci.send_seq, 100)
        self.assertEqual(apci.recv_seq, 200)

    def test_create_s_frame(self):
        """测试创建S格式帧"""
        apci = APCI.create_s_frame(150)
        self.assertEqual(apci.format_type, APCIType.S_FORMAT)
        self.assertEqual(apci.recv_seq, 150)

    def test_create_u_frame(self):
        """测试创建U格式帧"""
        apci = APCI.create_u_frame(UType.STARTDT_ACT)
        self.assertEqual(apci.format_type, APCIType.U_FORMAT)
        self.assertEqual(apci.utype, UType.STARTDT_ACT)

    def test_apci_encode_decode(self):
        """测试APCI编码和解码"""
        original = APCI.create_i_frame(123, 456)
        data = original.to_bytes()
        decoded = APCI.from_bytes(data)

        self.assertEqual(decoded.format_type, original.format_type)
        self.assertEqual(decoded.send_seq, original.send_seq)
        self.assertEqual(decoded.recv_seq, original.recv_seq)


class TestInformationObjects(unittest.TestCase):
    """信息对象测试"""

    def test_single_point_encode_decode(self):
        """测试单点信息编码解码"""
        obj = SinglePointInformation(ioa=100, value=True, quality=0)
        data = obj.encode(ioa_size=3)
        decoded = SinglePointInformation.decode(data, ioa_size=3)

        self.assertEqual(decoded.ioa, obj.ioa)
        self.assertEqual(decoded.value, obj.value)
        self.assertEqual(decoded.quality, obj.quality)

    def test_double_point_encode_decode(self):
        """测试双点信息编码解码"""
        obj = DoublePointInformation(ioa=200, value=2, quality=0)
        data = obj.encode(ioa_size=3)
        decoded = DoublePointInformation.decode(data, ioa_size=3)

        self.assertEqual(decoded.ioa, obj.ioa)
        self.assertEqual(decoded.value, obj.value)
        self.assertEqual(decoded.quality, obj.quality)

    def test_normalized_value_encode_decode(self):
        """测试归一化值编码解码"""
        obj = MeasuredValueNormalized(ioa=1000, value=0.5, quality=0)
        data = obj.encode(ioa_size=3)
        decoded = MeasuredValueNormalized.decode(data, ioa_size=3)

        self.assertEqual(decoded.ioa, obj.ioa)
        self.assertAlmostEqual(decoded.value, obj.value, places=4)
        self.assertEqual(decoded.quality, obj.quality)

    def test_scaled_value_encode_decode(self):
        """测试标度化值编码解码"""
        obj = MeasuredValueScaled(ioa=2000, value=12345, quality=0)
        data = obj.encode(ioa_size=3)
        decoded = MeasuredValueScaled.decode(data, ioa_size=3)

        self.assertEqual(decoded.ioa, obj.ioa)
        self.assertEqual(decoded.value, obj.value)
        self.assertEqual(decoded.quality, obj.quality)

    def test_float_value_encode_decode(self):
        """测试短浮点值编码解码"""
        obj = MeasuredValueFloat(ioa=3000, value=123.45, quality=0)
        data = obj.encode(ioa_size=3)
        decoded = MeasuredValueFloat.decode(data, ioa_size=3)

        self.assertEqual(decoded.ioa, obj.ioa)
        self.assertAlmostEqual(decoded.value, obj.value, places=2)
        self.assertEqual(decoded.quality, obj.quality)


class TestASDE(unittest.TestCase):
    """ASDU测试"""

    def test_create_asdu(self):
        """测试创建ASDU"""
        asdu = ASDU(TypeID.M_SP_NA_1, COT.SPONT, 0, 1)
        self.assertEqual(asdu.type_id, TypeID.M_SP_NA_1)
        self.assertEqual(asdu.cot, COT.SPONT)
        self.assertEqual(asdu.ca, 1)

    def test_add_information_objects(self):
        """测试添加信息对象"""
        asdu = ASDU(TypeID.M_SP_NA_1, COT.SPONT, 0, 1)

        obj1 = SinglePointInformation(1, True, 0)
        obj2 = SinglePointInformation(2, False, 0)

        asdu.add_information_object(obj1)
        asdu.add_information_object(obj2)

        self.assertEqual(asdu.num_objects, 2)
        self.assertEqual(len(asdu.information_objects), 2)

    def test_asdu_encode(self):
        """测试ASDU编码"""
        asdu = ASDU(TypeID.M_SP_NA_1, COT.SPONT, 0, 1)
        obj = SinglePointInformation(100, True, 0)
        asdu.add_information_object(obj)

        data = asdu.encode()
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestAPCI))
    suite.addTests(loader.loadTestsFromTestCase(TestInformationObjects))
    suite.addTests(loader.loadTestsFromTestCase(TestASDE))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
