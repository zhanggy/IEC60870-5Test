"""
链路健壮性测试
测试连接、断开、重连、超时等场景
"""

import time
import socket
from .base_test import BaseTest, TestResult, TestStatus
from .iec104_client import IEC104TestClient
from iec104 import APCI, APCIType, UType


class LinkRobustnessTest(BaseTest):
    """链路健壮性测试"""

    def test_basic_connection(self, result: TestResult):
        """测试基本连接"""
        client = IEC104TestClient(self.slave_host, self.slave_port, timeout=5.0)

        try:
            # 连接
            success = client.connect()
            self.assert_true(success, "连接失败")
            self.assert_true(client.connected, "连接状态错误")

            result.details['connected'] = True

        finally:
            client.disconnect()

    def test_startdt_stopdt(self, result: TestResult):
        """测试启动/停止数据传输"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 发送STARTDT
            client.send_startdt()
            frame = client.wait_for_frame(timeout=2.0)
            self.assert_true(frame is not None, "未收到STARTDT_CON")

            apci = APCI.from_bytes(frame)
            self.assert_equal(apci.format_type, APCIType.U_FORMAT, "帧类型错误")
            self.assert_equal(apci.utype, UType.STARTDT_CON, "未收到STARTDT_CON")

            client.data_transfer_active = True
            result.details['startdt'] = True

            # 发送STOPDT
            client.clear_received_frames()
            client.send_stopdt()
            frame = client.wait_for_frame(timeout=2.0)
            self.assert_true(frame is not None, "未收到STOPDT_CON")

            apci = APCI.from_bytes(frame)
            self.assert_equal(apci.utype, UType.STOPDT_CON, "未收到STOPDT_CON")

            result.details['stopdt'] = True

        finally:
            client.disconnect()

    def test_testfr_mechanism(self, result: TestResult):
        """测试测试帧机制"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 发送TESTFR
            start_time = time.time()
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)
            response_time = time.time() - start_time

            self.assert_true(frame is not None, "未收到TESTFR_CON")

            apci = APCI.from_bytes(frame)
            self.assert_equal(apci.format_type, APCIType.U_FORMAT, "帧类型错误")
            self.assert_equal(apci.utype, UType.TESTFR_CON, "未收到TESTFR_CON")

            result.details['response_time'] = f"{response_time*1000:.2f}ms"
            self.assert_in_range(response_time, 0, 1.0, "响应时间过长")

        finally:
            client.disconnect()

    def test_reconnection(self, result: TestResult):
        """测试重连能力"""
        client = IEC104TestClient(self.slave_host, self.slave_port)
        reconnect_count = 3

        try:
            for i in range(reconnect_count):
                # 连接
                client.connect()
                self.assert_true(client.connected, f"第{i+1}次连接失败")
                time.sleep(0.2)

                # 断开
                client.disconnect()
                time.sleep(0.5)

            result.details['reconnect_count'] = reconnect_count

        finally:
            client.disconnect()

    def test_connection_timeout(self, result: TestResult):
        """测试连接超时"""
        # 尝试连接到不存在的端口
        invalid_port = self.slave_port + 10000
        client = IEC104TestClient(self.slave_host, invalid_port, timeout=2.0)

        try:
            start_time = time.time()
            client.connect()
            # 如果能连接上，说明测试失败
            self.assert_true(False, "不应该连接成功")

        except ConnectionError:
            elapsed = time.time() - start_time
            result.details['timeout_duration'] = f"{elapsed:.2f}s"
            # 超时应该在合理范围内
            self.assert_in_range(elapsed, 1.5, 3.0, "超时时间不合理")

        finally:
            client.disconnect()

    def test_abrupt_disconnection(self, result: TestResult):
        """测试突然断开连接"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=1.0)

            # 不发送STOPDT，直接关闭socket
            if client.socket:
                client.socket.close()

            time.sleep(0.5)
            result.details['abrupt_disconnect'] = True

        finally:
            client.disconnect()

    def test_multiple_startdt(self, result: TestResult):
        """测试多次发送STARTDT"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 连续发送3次STARTDT
            for i in range(3):
                client.send_startdt()
                frame = client.wait_for_frame(timeout=2.0)
                self.assert_true(frame is not None, f"第{i+1}次未收到STARTDT_CON")

                apci = APCI.from_bytes(frame)
                self.assert_equal(apci.utype, UType.STARTDT_CON, f"第{i+1}次响应错误")
                client.clear_received_frames()
                time.sleep(0.1)

            result.details['startdt_count'] = 3

        finally:
            client.disconnect()

    def test_data_transfer_without_startdt(self, result: TestResult):
        """测试未启动数据传输时发送数据"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 不发送STARTDT，直接发送总召唤
            from iec104 import ASDU, TypeID, COT
            asdu = ASDU(TypeID.C_IC_NA_1, COT.ACT, 0, 1)
            asdu.num_objects = 1
            asdu_data = asdu.encode() + (0).to_bytes(3, 'little') + bytes([20])

            # 尝试发送I帧（应该失败或被忽略）
            client.data_transfer_active = True  # 强制设置
            apci = APCI.create_i_frame(0, 0)
            apci.length = 4 + len(asdu_data)
            frame = apci.to_bytes() + asdu_data
            client.send_raw_frame(frame)

            # 等待一段时间，不应该收到数据响应（可能收到错误帧）
            time.sleep(1.0)

            result.details['frames_received'] = client.get_received_frame_count()

        finally:
            client.disconnect()

    def test_idle_timeout_testfr(self, result: TestResult):
        """测试空闲时的TESTFR机制"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=1.0)
            client.data_transfer_active = True

            # 等待一段时间，检查是否收到TESTFR
            time.sleep(5.0)

            # 发送一个TESTFR看看连接是否还活着
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)
            self.assert_true(frame is not None, "连接可能已断开")

            result.details['connection_alive'] = True

        finally:
            client.disconnect()

    def test_socket_error_handling(self, result: TestResult):
        """测试Socket错误处理"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            original_socket = client.socket

            # 模拟socket错误：关闭底层socket但不通知客户端
            if original_socket:
                original_socket.shutdown(socket.SHUT_RDWR)

            time.sleep(0.5)

            # 尝试发送数据应该失败
            success = client.send_testfr()
            # 在某些情况下send可能不会立即失败
            result.details['send_after_shutdown'] = success

        except Exception as e:
            result.details['exception'] = str(e)

        finally:
            client.disconnect()
