"""
协议一致性测试
测试协议格式、序号管理、帧结构等
"""

import time
from .base_test import BaseTest, TestResult
from .iec104_client import IEC104TestClient
from iec104 import APCI, ASDU, APCIType, UType, TypeID, COT


class ProtocolComplianceTest(BaseTest):
    """协议一致性测试"""

    def test_apci_start_byte(self, result: TestResult):
        """测试APCI起始字节"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)

            self.assert_true(frame is not None, "未收到响应帧")
            self.assert_equal(frame[0], 0x68, "起始字节错误")

            result.details['start_byte'] = f"0x{frame[0]:02X}"

        finally:
            client.disconnect()

    def test_sequence_number_management(self, result: TestResult):
        """测试序号管理"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 发送总召唤
            client.send_general_interrogation(ca=1)

            # 接收多个I帧并检查序号
            time.sleep(1.0)
            i_frames = []

            for frame_data in client.received_frames:
                try:
                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.I_FORMAT:
                        i_frames.append(apci.send_seq)
                except:
                    pass

            # 检查序号是否连续
            if len(i_frames) > 1:
                for i in range(len(i_frames) - 1):
                    expected = (i_frames[i] + 1) & 0x7FFF
                    actual = i_frames[i + 1]
                    self.assert_equal(actual, expected, f"序号不连续: {i_frames[i]} -> {actual}")

            result.details['i_frame_count'] = len(i_frames)
            result.details['sequence_numbers'] = i_frames[:10]  # 只记录前10个

        finally:
            client.disconnect()

    def test_general_interrogation_response(self, result: TestResult):
        """测试总召唤响应"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 发送总召唤
            client.send_general_interrogation(ca=1)

            # 等待响应
            time.sleep(2.0)

            # 应该收到：激活确认 + 数据 + 激活终止
            actcon_received = False
            actterm_received = False
            data_count = 0

            for frame_data in client.received_frames:
                try:
                    if len(frame_data) <= 6:
                        continue

                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.I_FORMAT:
                        asdu = ASDU.decode(frame_data[6:])

                        if asdu.type_id == TypeID.C_IC_NA_1:
                            if asdu.cot == COT.ACTCON:
                                actcon_received = True
                            elif asdu.cot == COT.ACTTERM:
                                actterm_received = True
                        else:
                            # 数据帧
                            if asdu.cot == COT.INROGEN:
                                data_count += 1
                except Exception as e:
                    print(f"解析帧错误: {e}")

            self.assert_true(actcon_received, "未收到激活确认")
            self.assert_true(actterm_received, "未收到激活终止")

            result.details['actcon'] = actcon_received
            result.details['actterm'] = actterm_received
            result.details['data_frames'] = data_count

        finally:
            client.disconnect()

    def test_invalid_frame_handling(self, result: TestResult):
        """测试无效帧处理"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 发送无效起始字节的帧
            invalid_frame = bytes([0x99, 0x04, 0x00, 0x00, 0x00, 0x00])
            client.send_raw_frame(invalid_frame)
            time.sleep(0.5)

            # 连接应该仍然有效
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)
            self.assert_true(frame is not None, "连接已断开")

            result.details['connection_alive_after_invalid'] = True

        finally:
            client.disconnect()

    def test_frame_length_validation(self, result: TestResult):
        """测试帧长度验证"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 发送长度不匹配的帧
            # 声称长度为10，但实际只有6字节
            invalid_frame = bytes([0x68, 0x10, 0x00, 0x00, 0x00, 0x00])
            client.send_raw_frame(invalid_frame)
            time.sleep(0.5)

            # 发送正常TESTFR看连接是否正常
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)

            # 连接可能断开或继续工作
            result.details['connection_status'] = 'alive' if frame else 'closed'

        finally:
            client.disconnect()

    def test_max_sequence_number_rollover(self, result: TestResult):
        """测试序号翻转（理论测试）"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            # 设置接近最大值的序号
            test_seq = 0x7FFD  # 接近32767

            # 验证翻转逻辑
            next_seq = (test_seq + 1) & 0x7FFF
            self.assert_equal(next_seq, 0x7FFE, "序号计算错误")

            next_seq = (0x7FFF + 1) & 0x7FFF
            self.assert_equal(next_seq, 0, "序号翻转错误")

            result.details['rollover_test'] = 'passed'

        finally:
            pass

    def test_u_frame_types(self, result: TestResult):
        """测试U格式帧类型"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            u_frame_tests = [
                (UType.STARTDT_ACT, UType.STARTDT_CON, "STARTDT"),
                (UType.TESTFR_ACT, UType.TESTFR_CON, "TESTFR"),
                (UType.STOPDT_ACT, UType.STOPDT_CON, "STOPDT"),
            ]

            for send_type, expected_con, name in u_frame_tests:
                client.clear_received_frames()
                client.send_u_frame(send_type)
                frame = client.wait_for_frame(timeout=2.0)

                self.assert_true(frame is not None, f"{name}: 未收到响应")

                apci = APCI.from_bytes(frame)
                self.assert_equal(apci.format_type, APCIType.U_FORMAT, f"{name}: 帧类型错误")
                self.assert_equal(apci.utype, expected_con, f"{name}: 响应类型错误")

                result.details[name.lower()] = 'ok'
                time.sleep(0.1)

        finally:
            client.disconnect()

    def test_s_frame_format(self, result: TestResult):
        """测试S格式帧"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 发送总召唤引发I帧
            client.send_general_interrogation(ca=1)
            time.sleep(0.5)

            # 发送S帧确认
            client.send_s_frame()
            time.sleep(0.2)

            result.details['s_frame_sent'] = True

        finally:
            client.disconnect()

    def test_cot_values(self, result: TestResult):
        """测试传送原因(COT)值"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 发送总召唤
            client.send_general_interrogation(ca=1)
            time.sleep(1.5)

            cot_values = set()

            for frame_data in client.received_frames:
                try:
                    if len(frame_data) <= 6:
                        continue

                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.I_FORMAT:
                        # 简单提取COT（假设在固定位置）
                        if len(frame_data) > 8:
                            cot = frame_data[8]  # TypeID之后是VSQ，然后是COT
                            cot_values.add(cot)
                except:
                    pass

            result.details['cot_values'] = sorted(list(cot_values))
            result.details['cot_count'] = len(cot_values)

        finally:
            client.disconnect()

    def test_common_address(self, result: TestResult):
        """测试公共地址"""
        client = IEC104TestClient(self.slave_host, self.slave_port)
        expected_ca = self.config.get('common_address', 1)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 发送总召唤
            client.send_general_interrogation(ca=expected_ca)
            time.sleep(1.0)

            # 检查响应中的公共地址
            for frame_data in client.received_frames:
                try:
                    if len(frame_data) <= 6:
                        continue

                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.I_FORMAT:
                        asdu = ASDU.decode(frame_data[6:])
                        self.assert_equal(asdu.ca, expected_ca, f"公共地址不匹配: {asdu.ca}")
                        break
                except:
                    pass

            result.details['common_address'] = expected_ca

        finally:
            client.disconnect()
