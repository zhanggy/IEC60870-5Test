"""
IEC104测试客户端
用于测试框架的客户端实现
"""

import socket
import time
import threading
from typing import Optional, List, Callable
from iec104 import APCI, ASDU, APCIType, UType, TypeID, COT


class IEC104TestClient:
    """IEC104测试客户端"""

    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.data_transfer_active = False

        self.send_seq = 0
        self.recv_seq = 0

        # 接收缓冲
        self.recv_buffer = bytearray()
        self.received_frames: List[bytes] = []

        # 接收线程
        self.recv_thread: Optional[threading.Thread] = None
        self.running = False

        # 回调函数
        self.on_frame_received: Optional[Callable] = None

    def connect(self) -> bool:
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True

            # 启动接收线程
            self.running = True
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()

            return True
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"连接失败: {e}")

    def disconnect(self):
        """断开连接"""
        self.running = False
        self.connected = False
        self.data_transfer_active = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def _recv_loop(self):
        """接收循环"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.connected = False
                    break

                self.recv_buffer.extend(data)
                self._process_buffer()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"接收错误: {e}")
                break

    def _process_buffer(self):
        """处理接收缓冲"""
        while len(self.recv_buffer) >= 2:
            if self.recv_buffer[0] != 0x68:
                self.recv_buffer.pop(0)
                continue

            length = self.recv_buffer[1]
            total_length = length + 2

            if len(self.recv_buffer) < total_length:
                break

            frame = bytes(self.recv_buffer[:total_length])
            self.recv_buffer = self.recv_buffer[total_length:]

            self.received_frames.append(frame)

            # 更新接收序号
            try:
                apci = APCI.from_bytes(frame)
                if apci.format_type == APCIType.I_FORMAT:
                    self.recv_seq = (apci.send_seq + 1) & 0x7FFF
            except:
                pass

            if self.on_frame_received:
                self.on_frame_received(frame)

    def send_startdt(self) -> bool:
        """发送启动数据传输"""
        return self.send_u_frame(UType.STARTDT_ACT)

    def send_stopdt(self) -> bool:
        """发送停止数据传输"""
        return self.send_u_frame(UType.STOPDT_ACT)

    def send_testfr(self) -> bool:
        """发送测试帧"""
        return self.send_u_frame(UType.TESTFR_ACT)

    def send_u_frame(self, utype: int) -> bool:
        """发送U格式帧"""
        if not self.connected:
            return False

        try:
            apci = APCI.create_u_frame(utype)
            self.socket.sendall(apci.to_bytes())
            return True
        except Exception as e:
            print(f"发送U帧错误: {e}")
            return False

    def send_s_frame(self) -> bool:
        """发送S格式帧"""
        if not self.connected:
            return False

        try:
            apci = APCI.create_s_frame(self.recv_seq)
            self.socket.sendall(apci.to_bytes())
            return True
        except Exception as e:
            print(f"发送S帧错误: {e}")
            return False

    def send_general_interrogation(self, ca: int = 1) -> bool:
        """发送总召唤"""
        asdu = ASDU(TypeID.C_IC_NA_1, COT.ACT, 0, ca)
        asdu.num_objects = 1

        # IOA=0表示全站召唤
        ioa_bytes = (0).to_bytes(3, 'little')
        qoi = 20  # 总召唤
        asdu_data = asdu.encode() + ioa_bytes + bytes([qoi])

        return self.send_i_frame(asdu_data)

    def send_i_frame(self, asdu_data: bytes) -> bool:
        """发送I格式帧"""
        if not self.connected or not self.data_transfer_active:
            return False

        try:
            apci = APCI.create_i_frame(self.send_seq, self.recv_seq)
            apci.length = 4 + len(asdu_data)

            frame = apci.to_bytes() + asdu_data
            self.socket.sendall(frame)
            self.send_seq = (self.send_seq + 1) & 0x7FFF
            return True
        except Exception as e:
            print(f"发送I帧错误: {e}")
            return False

    def send_raw_frame(self, data: bytes) -> bool:
        """发送原始帧（用于错误注入测试）"""
        if not self.connected:
            return False

        try:
            self.socket.sendall(data)
            return True
        except Exception as e:
            print(f"发送原始帧错误: {e}")
            return False

    def wait_for_frame(self, timeout: float = 5.0, frame_type: Optional[int] = None) -> Optional[bytes]:
        """等待接收帧"""
        start_time = time.time()
        initial_count = len(self.received_frames)

        while time.time() - start_time < timeout:
            if len(self.received_frames) > initial_count:
                frame = self.received_frames[-1]

                if frame_type is None:
                    return frame

                try:
                    apci = APCI.from_bytes(frame)
                    if apci.format_type == frame_type:
                        return frame
                    elif frame_type == APCIType.U_FORMAT and apci.format_type == APCIType.U_FORMAT:
                        return frame
                except:
                    pass

            time.sleep(0.01)

        return None

    def clear_received_frames(self):
        """清除已接收的帧"""
        self.received_frames.clear()

    def get_received_frame_count(self) -> int:
        """获取接收帧数量"""
        return len(self.received_frames)

    def reset_sequence_numbers(self):
        """重置序号"""
        self.send_seq = 0
        self.recv_seq = 0
