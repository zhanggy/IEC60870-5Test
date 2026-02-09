"""
性能测试
测试响应时间、吞吐量等性能指标
"""

import time
from typing import List
from .base_test import BaseTest, TestResult
from .iec104_client import IEC104TestClient
from iec104 import APCI, APCIType


class PerformanceTest(BaseTest):
    """性能测试"""

    def test_connection_establishment_time(self, result: TestResult):
        """测试连接建立时间"""
        times: List[float] = []
        iterations = 10

        for i in range(iterations):
            client = IEC104TestClient(self.slave_host, self.slave_port)
            try:
                start = time.time()
                client.connect()
                elapsed = time.time() - start
                times.append(elapsed)
            finally:
                client.disconnect()
                time.sleep(0.1)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        result.details['average_time'] = f"{avg_time*1000:.2f}ms"
        result.details['min_time'] = f"{min_time*1000:.2f}ms"
        result.details['max_time'] = f"{max_time*1000:.2f}ms"
        result.details['iterations'] = iterations

        # 平均连接时间应该小于500ms
        self.assert_in_range(avg_time, 0, 0.5, "连接时间过长")

    def test_testfr_response_time(self, result: TestResult):
        """测试TESTFR响应时间"""
        client = IEC104TestClient(self.slave_host, self.slave_port)
        times: List[float] = []
        iterations = 20

        try:
            client.connect()
            time.sleep(0.1)

            for i in range(iterations):
                client.clear_received_frames()
                start = time.time()
                client.send_testfr()
                frame = client.wait_for_frame(timeout=2.0)
                elapsed = time.time() - start

                self.assert_true(frame is not None, f"第{i+1}次未收到响应")
                times.append(elapsed)
                time.sleep(0.05)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            result.details['average_response'] = f"{avg_time*1000:.2f}ms"
            result.details['min_response'] = f"{min_time*1000:.2f}ms"
            result.details['max_response'] = f"{max_time*1000:.2f}ms"
            result.details['iterations'] = iterations

            # 平均响应时间应该小于100ms
            self.assert_in_range(avg_time, 0, 0.1, "响应时间过长")

        finally:
            client.disconnect()

    def test_general_interrogation_response_time(self, result: TestResult):
        """测试总召唤响应时间"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            time.sleep(0.1)

            # 测试3次总召唤
            times: List[float] = []

            for i in range(3):
                client.clear_received_frames()
                start = time.time()
                client.send_general_interrogation(ca=1)

                # 等待激活终止
                timeout = 5.0
                actterm_received = False

                while time.time() - start < timeout:
                    time.sleep(0.1)
                    for frame_data in client.received_frames:
                        try:
                            if len(frame_data) > 6:
                                # 检查是否是激活终止
                                if frame_data[6] == 100:  # TypeID C_IC_NA_1
                                    cot = frame_data[8]
                                    if cot == 10:  # ACTTERM
                                        actterm_received = True
                                        break
                        except:
                            pass

                    if actterm_received:
                        break

                elapsed = time.time() - start
                self.assert_true(actterm_received, f"第{i+1}次未收到激活终止")
                times.append(elapsed)
                time.sleep(0.5)

            avg_time = sum(times) / len(times)
            result.details['average_gi_time'] = f"{avg_time*1000:.2f}ms"
            result.details['iterations'] = len(times)

            # 总召唤应该在3秒内完成
            self.assert_in_range(avg_time, 0, 3.0, "总召唤时间过长")

        finally:
            client.disconnect()

    def test_data_throughput(self, result: TestResult):
        """测试数据吞吐量"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 触发总召唤获取大量数据
            start = time.time()
            client.send_general_interrogation(ca=1)
            time.sleep(2.0)
            elapsed = time.time() - start

            frame_count = client.get_received_frame_count()
            total_bytes = sum(len(f) for f in client.received_frames)

            throughput_fps = frame_count / elapsed if elapsed > 0 else 0
            throughput_bps = total_bytes / elapsed if elapsed > 0 else 0

            result.details['frames_received'] = frame_count
            result.details['total_bytes'] = total_bytes
            result.details['duration'] = f"{elapsed:.2f}s"
            result.details['throughput_fps'] = f"{throughput_fps:.2f} frames/s"
            result.details['throughput_bps'] = f"{throughput_bps:.2f} bytes/s"

        finally:
            client.disconnect()

    def test_sequence_number_performance(self, result: TestResult):
        """测试序号处理性能"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True
            client.clear_received_frames()

            # 发送总召唤
            start = time.time()
            client.send_general_interrogation(ca=1)
            time.sleep(1.5)
            elapsed = time.time() - start

            # 统计I帧序号处理
            i_frame_count = 0
            sequence_errors = 0
            last_seq = None

            for frame_data in client.received_frames:
                try:
                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.I_FORMAT:
                        i_frame_count += 1
                        if last_seq is not None:
                            expected = (last_seq + 1) & 0x7FFF
                            if apci.send_seq != expected:
                                sequence_errors += 1
                        last_seq = apci.send_seq
                except:
                    pass

            result.details['i_frames'] = i_frame_count
            result.details['sequence_errors'] = sequence_errors
            result.details['processing_rate'] = f"{i_frame_count/elapsed:.2f} frames/s"

            self.assert_equal(sequence_errors, 0, "序号处理错误")

        finally:
            client.disconnect()

    def test_concurrent_testfr(self, result: TestResult):
        """测试并发TESTFR性能"""
        client = IEC104TestClient(self.slave_host, self.slave_port)

        try:
            client.connect()
            time.sleep(0.1)

            # 快速连续发送TESTFR
            count = 10
            start = time.time()

            for _ in range(count):
                client.send_testfr()
                time.sleep(0.01)  # 10ms间隔

            # 等待所有响应
            time.sleep(1.0)
            elapsed = time.time() - start

            # 检查收到的响应数量
            testfr_con_count = 0
            for frame_data in client.received_frames:
                try:
                    apci = APCI.from_bytes(frame_data)
                    if apci.format_type == APCIType.U_FORMAT and apci.utype == 0x83:
                        testfr_con_count += 1
                except:
                    pass

            result.details['sent_count'] = count
            result.details['received_count'] = testfr_con_count
            result.details['duration'] = f"{elapsed:.2f}s"

            # 应该收到所有响应
            self.assert_equal(testfr_con_count, count, "响应数量不匹配")

        finally:
            client.disconnect()

    def test_memory_leak_detection(self, result: TestResult):
        """测试内存泄漏（简单检测）"""
        import gc
        gc.collect()

        initial_objects = len(gc.get_objects())

        # 执行多次连接/断开循环
        for _ in range(20):
            client = IEC104TestClient(self.slave_host, self.slave_port)
            try:
                client.connect()
                client.send_testfr()
                client.wait_for_frame(timeout=1.0)
            finally:
                client.disconnect()
            time.sleep(0.05)

        gc.collect()
        final_objects = len(gc.get_objects())

        object_increase = final_objects - initial_objects

        result.details['initial_objects'] = initial_objects
        result.details['final_objects'] = final_objects
        result.details['object_increase'] = object_increase

        # 对象增长应该在合理范围内（小于1000）
        self.assert_in_range(object_increase, -100, 1000, "可能存在内存泄漏")

    def test_sustained_load(self, result: TestResult):
        """测试持续负载"""
        client = IEC104TestClient(self.slave_host, self.slave_port)
        duration = 5  # 5秒测试
        operations = 0

        try:
            client.connect()
            client.send_startdt()
            client.wait_for_frame(timeout=2.0)
            client.data_transfer_active = True

            start = time.time()
            end_time = start + duration

            while time.time() < end_time:
                client.send_testfr()
                time.sleep(0.1)
                operations += 1

            elapsed = time.time() - start

            result.details['duration'] = f"{elapsed:.2f}s"
            result.details['operations'] = operations
            result.details['ops_per_second'] = f"{operations/elapsed:.2f}"

            # 连接应该仍然有效
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)
            self.assert_true(frame is not None, "持续负载后连接失效")

        finally:
            client.disconnect()
