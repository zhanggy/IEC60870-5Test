"""
IEC60870-5-104 Slave服务器
主服务器类，负责监听连接和管理客户端
"""

import socket
import threading
import logging
import json
from typing import List
from connection_handler import ConnectionHandler
from data_manager import DataPointManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IEC104SlaveServer:
    """IEC60870-5-104 Slave服务器"""

    def __init__(self, config_file: str = 'config.json'):
        """
        初始化服务器

        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 服务器配置
        server_config = self.config.get('server', {})
        self.host = server_config.get('host', '0.0.0.0')
        self.port = server_config.get('port', 2404)
        self.max_connections = server_config.get('max_connections', 5)

        # 数据点管理器
        self.data_manager = DataPointManager()
        self.data_manager.load_from_config(self.config)

        # 服务器状态
        self.is_running = False
        self.server_socket = None
        self.accept_thread = None

        # 连接管理
        self.connections: List[ConnectionHandler] = []
        self.connections_lock = threading.Lock()

        logger.info("IEC104 Slave服务器初始化完成")
        logger.info(f"监听地址: {self.host}:{self.port}")
        logger.info(f"最大连接数: {self.max_connections}")

    def start(self):
        """启动服务器"""
        if self.is_running:
            logger.warning("服务器已在运行")
            return

        try:
            # 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)

            self.is_running = True

            # 启动接受连接线程
            self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.accept_thread.start()

            logger.info("服务器启动成功")

        except Exception as e:
            logger.error(f"服务器启动失败: {e}", exc_info=True)
            self.stop()

    def stop(self):
        """停止服务器"""
        if not self.is_running:
            return

        logger.info("正在停止服务器...")
        self.is_running = False

        # 关闭所有连接
        with self.connections_lock:
            for conn in self.connections:
                conn.stop()
            self.connections.clear()

        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

        logger.info("服务器已停止")

    def _accept_loop(self):
        """接受连接循环"""
        logger.info("开始监听连接...")

        while self.is_running:
            try:
                # 接受客户端连接
                client_socket, address = self.server_socket.accept()

                # 检查连接数量
                with self.connections_lock:
                    if len(self.connections) >= self.max_connections:
                        logger.warning(f"连接数已达上限，拒绝连接: {address}")
                        client_socket.close()
                        continue

                    # 创建连接处理器
                    handler = ConnectionHandler(client_socket, address,
                                               self.data_manager, self.config)
                    handler.start()
                    self.connections.append(handler)

                    logger.info(f"接受新连接: {address}, 当前连接数: {len(self.connections)}")

            except Exception as e:
                if self.is_running:
                    logger.error(f"接受连接错误: {e}", exc_info=True)

        logger.info("停止监听连接")

    def update_data_point(self, point_type: str, ioa: int, value, quality: int = 0):
        """
        更新数据点值

        Args:
            point_type: 数据点类型 ('single', 'double', 'normalized', 'scaled', 'float')
            ioa: 信息对象地址
            value: 值
            quality: 品质描述词
        """
        if point_type == 'single':
            self.data_manager.set_single_point(ioa, value, quality)
        elif point_type == 'double':
            self.data_manager.set_double_point(ioa, value, quality)
        else:
            logger.warning(f"不支持的数据点类型: {point_type}")

    def get_data_point(self, point_type: str, ioa: int):
        """
        获取数据点值

        Args:
            point_type: 数据点类型
            ioa: 信息对象地址

        Returns:
            (value, quality) 或 None
        """
        if point_type == 'single':
            return self.data_manager.get_single_point(ioa)
        elif point_type == 'double':
            return self.data_manager.get_double_point(ioa)
        elif point_type == 'normalized':
            return self.data_manager.get_normalized_value(ioa)
        elif point_type == 'scaled':
            return self.data_manager.get_scaled_value(ioa)
        elif point_type == 'float':
            return self.data_manager.get_float_value(ioa)
        else:
            logger.warning(f"不支持的数据点类型: {point_type}")
            return None

    def get_active_connections_count(self) -> int:
        """获取活动连接数"""
        with self.connections_lock:
            return len(self.connections)


def main():
    """主函数"""
    import sys

    # 解析命令行参数
    config_file = 'config.json'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    # 创建并启动服务器
    server = IEC104SlaveServer(config_file)
    server.start()

    try:
        print("=" * 60)
        print("IEC60870-5-104 Slave测试服务器")
        print("=" * 60)
        print(f"监听地址: {server.host}:{server.port}")
        print("服务器正在运行，按 Ctrl+C 停止")
        print("=" * 60)

        # 保持运行
        while True:
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n收到停止信号")
    finally:
        server.stop()
        print("服务器已退出")


if __name__ == '__main__':
    main()
