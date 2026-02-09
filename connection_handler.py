"""
IEC60870-5-104 Slave连接处理器
处理单个客户端连接
"""

import socket
import threading
import logging
from typing import Optional
from iec104 import APCI, ASDU, APCIType, UType, TypeID, COT
from iec104 import (SinglePointInformation, DoublePointInformation,
                    MeasuredValueNormalized, MeasuredValueScaled,
                    MeasuredValueFloat)
from data_manager import DataPointManager


logger = logging.getLogger(__name__)


class ConnectionHandler:
    """连接处理器"""

    def __init__(self, client_socket: socket.socket, address: tuple,
                 data_manager: DataPointManager, config: dict):
        self.socket = client_socket
        self.address = address
        self.data_manager = data_manager
        self.config = config

        # 序号管理
        self.send_seq = 0
        self.recv_seq = 0

        # 状态管理
        self.is_running = False
        self.data_transfer_started = False

        # 线程
        self.recv_thread: Optional[threading.Thread] = None

        # 配置参数
        self.station_config = config.get('station', {})
        self.common_address = self.station_config.get('common_address', 1)
        self.cot_size = self.station_config.get('cot_size', 2)
        self.asdu_addr_size = self.station_config.get('asdu_address_size', 2)
        self.ioa_size = self.station_config.get('ioa_size', 3)

        logger.info(f"新连接来自 {address}")

    def start(self):
        """启动连接处理"""
        self.is_running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def stop(self):
        """停止连接处理"""
        self.is_running = False
        try:
            self.socket.close()
        except Exception:
            pass
        logger.info(f"连接关闭 {self.address}")

    def _recv_loop(self):
        """接收循环"""
        buffer = bytearray()

        try:
            while self.is_running:
                # 接收数据
                data = self.socket.recv(4096)
                if not data:
                    logger.info(f"客户端断开连接 {self.address}")
                    break

                buffer.extend(data)

                # 处理缓冲区中的完整帧
                while len(buffer) >= 2:
                    if buffer[0] != 0x68:
                        logger.warning(f"无效的起始字节: 0x{buffer[0]:02X}")
                        buffer.pop(0)
                        continue

                    length = buffer[1]
                    total_length = length + 2  # 包括起始字节和长度字节

                    if len(buffer) < total_length:
                        break  # 数据不完整，等待更多数据

                    # 提取完整帧
                    frame = bytes(buffer[:total_length])
                    buffer = buffer[total_length:]

                    # 处理帧
                    self._handle_frame(frame)

        except Exception as e:
            logger.error(f"接收循环错误: {e}", exc_info=True)
        finally:
            self.stop()

    def _handle_frame(self, frame: bytes):
        """处理帧"""
        try:
            apci = APCI.from_bytes(frame)
            logger.debug(f"收到: {apci}")

            if apci.format_type == APCIType.I_FORMAT:
                self._handle_i_frame(apci, frame[6:])
            elif apci.format_type == APCIType.S_FORMAT:
                self._handle_s_frame(apci)
            elif apci.format_type == APCIType.U_FORMAT:
                self._handle_u_frame(apci)

        except Exception as e:
            logger.error(f"处理帧错误: {e}", exc_info=True)

    def _handle_i_frame(self, apci: APCI, asdu_data: bytes):
        """处理I格式帧"""
        # 更新接收序号
        self.recv_seq = (apci.send_seq + 1) & 0x7FFF

        # 解析ASDU
        try:
            asdu = ASDU.decode(asdu_data, self.cot_size,
                             self.asdu_addr_size, self.ioa_size)
            logger.info(f"收到 ASDU: {asdu}")

            # 处理ASDU
            self._handle_asdu(asdu)

            # 发送S帧确认
            self._send_s_frame()

        except Exception as e:
            logger.error(f"处理I帧错误: {e}", exc_info=True)

    def _handle_s_frame(self, apci: APCI):
        """处理S格式帧"""
        logger.debug(f"收到S帧确认: recv_seq={apci.recv_seq}")

    def _handle_u_frame(self, apci: APCI):
        """处理U格式帧"""
        utype = apci.utype

        if utype == UType.STARTDT_ACT:
            # 启动数据传输激活
            logger.info("收到 STARTDT_ACT")
            self.data_transfer_started = True
            self._send_u_frame(UType.STARTDT_CON)

        elif utype == UType.STOPDT_ACT:
            # 停止数据传输激活
            logger.info("收到 STOPDT_ACT")
            self.data_transfer_started = False
            self._send_u_frame(UType.STOPDT_CON)

        elif utype == UType.TESTFR_ACT:
            # 测试帧激活
            logger.debug("收到 TESTFR_ACT")
            self._send_u_frame(UType.TESTFR_CON)

    def _handle_asdu(self, asdu: ASDU):
        """处理ASDU"""
        if asdu.type_id == TypeID.C_IC_NA_1:
            # 总召唤命令
            logger.info("收到总召唤命令")
            self._handle_general_interrogation(asdu)

        elif asdu.type_id == TypeID.C_SC_NA_1:
            # 单点命令
            logger.info("收到单点命令")
            self._handle_single_command(asdu)

        elif asdu.type_id == TypeID.C_DC_NA_1:
            # 双点命令
            logger.info("收到双点命令")
            self._handle_double_command(asdu)

        elif asdu.type_id == TypeID.C_RD_NA_1:
            # 读命令
            logger.info("收到读命令")
            self._handle_read_command(asdu)

    def _handle_general_interrogation(self, asdu: ASDU):
        """处理总召唤"""
        # 发送激活确认
        confirm_asdu = ASDU(TypeID.C_IC_NA_1, COT.ACTCON, 0,
                           self.common_address, self.cot_size,
                           self.asdu_addr_size, self.ioa_size)
        self._send_asdu(confirm_asdu)

        # 发送所有数据点
        self._send_all_data_points(COT.INROGEN)

        # 发送激活终止
        term_asdu = ASDU(TypeID.C_IC_NA_1, COT.ACTTERM, 0,
                        self.common_address, self.cot_size,
                        self.asdu_addr_size, self.ioa_size)
        self._send_asdu(term_asdu)

    def _handle_single_command(self, asdu: ASDU):
        """处理单点命令"""
        # 简化实现：发送激活确认
        confirm_asdu = ASDU(TypeID.C_SC_NA_1, COT.ACTCON, 0,
                           self.common_address, self.cot_size,
                           self.asdu_addr_size, self.ioa_size)
        self._send_asdu(confirm_asdu)

    def _handle_double_command(self, asdu: ASDU):
        """处理双点命令"""
        # 简化实现：发送激活确认
        confirm_asdu = ASDU(TypeID.C_DC_NA_1, COT.ACTCON, 0,
                           self.common_address, self.cot_size,
                           self.asdu_addr_size, self.ioa_size)
        self._send_asdu(confirm_asdu)

    def _handle_read_command(self, asdu: ASDU):
        """处理读命令"""
        # 简化实现：发送激活确认
        confirm_asdu = ASDU(TypeID.C_RD_NA_1, COT.ACTCON, 0,
                           self.common_address, self.cot_size,
                           self.asdu_addr_size, self.ioa_size)
        self._send_asdu(confirm_asdu)

    def _send_all_data_points(self, cot: int):
        """发送所有数据点"""
        # 发送所有单点信息
        single_points = self.data_manager.get_all_single_points()
        if single_points:
            asdu = ASDU(TypeID.M_SP_NA_1, cot, 0, self.common_address,
                       self.cot_size, self.asdu_addr_size, self.ioa_size)
            for ioa, (value, quality) in single_points.items():
                obj = SinglePointInformation(ioa, value, quality)
                asdu.add_information_object(obj)
            self._send_asdu(asdu)

        # 发送所有双点信息
        double_points = self.data_manager.get_all_double_points()
        if double_points:
            asdu = ASDU(TypeID.M_DP_NA_1, cot, 0, self.common_address,
                       self.cot_size, self.asdu_addr_size, self.ioa_size)
            for ioa, (value, quality) in double_points.items():
                obj = DoublePointInformation(ioa, value, quality)
                asdu.add_information_object(obj)
            self._send_asdu(asdu)

        # 发送所有归一化测量值
        normalized_values = self.data_manager.get_all_normalized_values()
        if normalized_values:
            asdu = ASDU(TypeID.M_ME_NA_1, cot, 0, self.common_address,
                       self.cot_size, self.asdu_addr_size, self.ioa_size)
            for ioa, (value, quality) in normalized_values.items():
                obj = MeasuredValueNormalized(ioa, value, quality)
                asdu.add_information_object(obj)
            self._send_asdu(asdu)

        # 发送所有标度化测量值
        scaled_values = self.data_manager.get_all_scaled_values()
        if scaled_values:
            asdu = ASDU(TypeID.M_ME_NB_1, cot, 0, self.common_address,
                       self.cot_size, self.asdu_addr_size, self.ioa_size)
            for ioa, (value, quality) in scaled_values.items():
                obj = MeasuredValueScaled(ioa, value, quality)
                asdu.add_information_object(obj)
            self._send_asdu(asdu)

        # 发送所有短浮点测量值
        float_values = self.data_manager.get_all_float_values()
        if float_values:
            asdu = ASDU(TypeID.M_ME_NC_1, cot, 0, self.common_address,
                       self.cot_size, self.asdu_addr_size, self.ioa_size)
            for ioa, (value, quality) in float_values.items():
                obj = MeasuredValueFloat(ioa, value, quality)
                asdu.add_information_object(obj)
            self._send_asdu(asdu)

    def _send_asdu(self, asdu: ASDU):
        """发送ASDU"""
        if not self.data_transfer_started:
            logger.warning("数据传输未启动，无法发送ASDU")
            return

        asdu_bytes = asdu.encode()
        apci = APCI.create_i_frame(self.send_seq, self.recv_seq)
        apci.length = 4 + len(asdu_bytes)

        frame = apci.to_bytes() + asdu_bytes

        try:
            self.socket.sendall(frame)
            self.send_seq = (self.send_seq + 1) & 0x7FFF
            logger.debug(f"发送 ASDU: {asdu}")
        except Exception as e:
            logger.error(f"发送ASDU错误: {e}")

    def _send_s_frame(self):
        """发送S格式帧"""
        apci = APCI.create_s_frame(self.recv_seq)
        try:
            self.socket.sendall(apci.to_bytes())
            logger.debug(f"发送S帧: recv_seq={self.recv_seq}")
        except Exception as e:
            logger.error(f"发送S帧错误: {e}")

    def _send_u_frame(self, utype: int):
        """发送U格式帧"""
        apci = APCI.create_u_frame(utype)
        try:
            self.socket.sendall(apci.to_bytes())
            logger.debug(f"发送U帧: {apci}")
        except Exception as e:
            logger.error(f"发送U帧错误: {e}")
