"""
压力测试
测试极限情况、高负载、多连接等
"""

import time
import threading
from typing import List
from .base_test import BaseTest, TestResult
from .iec104_client import IEC104TestClient


class StressTest(BaseTest):
    """压力测试"""

    def test_max_connections(self, result: TestResult):
        """测试最大连接数"""
        max_conn = self.config.get('max_connections', 5)
        clients: List[IEC104TestClient] = []

        try:
            # 尝试建立最大允许连接数
            for i in range(max_conn):
                client = IEC104TestClient(self.slave_host, self.slave_port)
                client.connect()
                clients.append(client)
                time.sleep(0.1)

            # 所有连接都应该成功
            self.assert_equal(len(clients), max_conn, "未能建立所有连接")

            # 尝试建立额外连接（应该被拒绝）
            extra_client = IEC104TestClient(self.slave_host, self.slave_port, timeout=2.0)
            try:
                extra_client.connect()
                time.sleep(0.5)

                # 如果连接成功，可能是配置更高或没有限制
                result.details['extra_connection'] = 'accepted'
                extra_client.disconnect()
            except:
                result.details['extra_connection'] = 'rejected'

            result.details['max_connections'] = max_conn
            result.details['established_connections'] = len(clients)

        finally:
            for client in clients:
                try:
                    client.disconnect()
                except:
                    pass

    def test_rapid_connect_disconnect(self, result: TestResult):
        """测试快速连接断开"""
        iterations = 50
        errors = 0

        for i in range(iterations):
            client = IEC104TestClient(self.slave_host, self.slave_port, timeout=2.0)
            try:
                client.connect()
                client.disconnect()
            except Exception as e:
                errors += 1
                if errors <= 3:  # 只记录前几个错误
                    result.details[f'error_{errors}'] = str(e)

            if i % 10 == 0:
                time.sleep(0.1)  # 偶尔休息一下

        result.details['iterations'] = iterations
        result.details['errors'] = errors
        result.details['success_rate'] = f"{(iterations-errors)/iterations*100:.1f}%"

        # 错误率应该小于5%
        self.assert_in_range(errors, 0, iterations * 0.05, "错误率过高")

    def test_large_data_volume(self, result: TestResult):
        """测试大数据量"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True

            # 连续多次总召唤
            gi_count = 10
            total_frames = 0

            for i in range(gi_count):
                client.clear_received_frames()
                client.send_general_interrogation(ca=1)
                time.sleep(1.0)
                total_frames += client.get_received_frame_count()

            result.details['general_interrogations'] = gi_count
            result.details['total_frames'] = total_frames
            result.details['avg_frames_per_gi'] = total_frames / gi_count

        finally:
            client.disconnect()

    def test_continuous_testfr_flood(self, result: TestResult):
        """测试TESTFR洪水攻击"""
        client = IEC104TestClient(self.slave_host, self.slave_port)
        duration = 3  # 3秒

        try:
            client.connect()
            time.sleep(0.1)

            start = time.time()
            sent_count = 0

            # 持续发送TESTFR尽可能快
            while time.time() - start < duration:
                client.send_testfr()
                sent_count += 1

            time.sleep(0.5)  # 等待响应

            result.details['duration'] = f"{duration}s"
            result.details['sent_count'] = sent_count
            result.details['rate'] = f"{sent_count/duration:.0f} frames/s"

            # 连接应该仍然有效
            client.clear_received_frames()
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)
            self.assert_true(frame is not None, "洪水攻击后连接失效")

        finally:
            client.disconnect()

    def test_malformed_frame_flood(self, result: TestResult):
        """测试畸形帧洪水"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 发送各种畸形帧
            malformed_frames = [
                bytes([0x68, 0x04, 0xFF, 0xFF, 0xFF, 0xFF]),  # 无效控制字段
                bytes([0x68, 0x10, 0x00, 0x00, 0x00, 0x00]),  # 长度不匹配
                bytes([0x68, 0x00, 0x00, 0x00, 0x00, 0x00]),  # 零长度
                bytes([0x68, 0x04]),  # 不完整
                bytes([0xFF] * 10),  # 完全无效
            ]

            for frame in malformed_frames:
                client.send_raw_frame(frame)
                time.sleep(0.05)

            time.sleep(0.5)

            # 检查连接是否仍然有效
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)

            result.details['malformed_sent'] = len(malformed_frames)
            result.details['connection_alive'] = frame is not None

        finally:
            client.disconnect()

    def test_concurrent_operations(self, result: TestResult):
        """测试并发操作"""
        num_clients = 3
        clients: List[IEC104TestClient] = []
        errors = []

        def client_operation(client_id: int):
            client = IEC104TestClient(self.slave_host, self.slave_port)
            clients.append(client)
            try:
                client.connect()
                time.sleep(0.1)

                # 每个客户端执行一系列操作
                for _ in range(5):
                    client.send_testfr()
                    time.sleep(0.2)

                client.send_startdt()
                time.sleep(0.5)
                client.data_transfer_active = True
                client.send_general_interrogation(ca=1)
                time.sleep(1.0)

            except Exception as e:
                errors.append(f"Client {client_id}: {str(e)}")

        # 启动多个客户端线程
        threads = []
        for i in range(num_clients):
            thread = threading.Thread(target=client_operation, args=(i,))
            thread.start()
            threads.append(thread)

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=10)

        result.details['concurrent_clients'] = num_clients
        result.details['errors'] = len(errors)
        if errors:
            result.details['error_samples'] = errors[:3]

        # 清理
        for client in clients:
            try:
                client.disconnect()
            except:
                pass

        self.assert_equal(len(errors), 0, f"并发操作出现{len(errors)}个错误")

    def test_sequence_number_stress(self, result: TestResult):
        """测试序号压力"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True

            # 快速发送多个总召唤以产生大量I帧
            for _ in range(10):
                client.send_general_interrogation(ca=1)
                time.sleep(0.1)

            time.sleep(2.0)

            # 检查序号一致性
            from iec104 import APCI, APCIType
            i_frames = []

            for frame_data in client.received_frames:
                try:
                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.I_FORMAT:
                        i_frames.append(apci.send_seq)
                except:
                    pass

            # 检查序号
            sequence_errors = 0
            for i in range(len(i_frames) - 1):
                expected = (i_frames[i] + 1) & 0x7FFF
                if i_frames[i + 1] != expected:
                    sequence_errors += 1

            result.details['i_frame_count'] = len(i_frames)
            result.details['sequence_errors'] = sequence_errors

            self.assert_equal(sequence_errors, 0, "序号管理错误")

        finally:
            client.disconnect()

    def test_long_running_connection(self, result: TestResult):
        """测试长时间连接"""
        client = IEC104TestClient(self.slave_host, self.slave_port)
        duration = 10  # 10秒

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True

            start = time.time()
            operations = 0

            while time.time() - start < duration:
                # 定期发送TESTFR
                client.send_testfr()
                time.sleep(1.0)
                operations += 1

            elapsed = time.time() - start

            # 最后验证连接
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)

            result.details['duration'] = f"{elapsed:.2f}s"
            result.details['operations'] = operations
            result.details['connection_alive'] = frame is not None

            self.assert_true(frame is not None, "长时间连接后失效")

        finally:
            client.disconnect()

    def test_buffer_overflow_protection(self, result: TestResult):
        """测试缓冲区溢出保护"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 发送超大帧
            large_frame = bytes([0x68, 0xFF]) + bytes([0x00] * 300)
            client.send_raw_frame(large_frame)
            time.sleep(0.5)

            # 检查连接
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)

            result.details['large_frame_sent'] = True
            result.details['connection_status'] = 'alive' if frame else 'closed'

        finally:
            client.disconnect()
