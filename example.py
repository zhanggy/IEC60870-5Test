"""
IEC60870-5-104 Slave服务器测试示例
演示如何使用服务器和动态更新数据点
"""

import time
import random
import threading
from slave_server import IEC104SlaveServer


def simulate_data_changes(server: IEC104SlaveServer):
    """
    模拟数据变化
    定期随机更新数据点的值
    """
    print("\n开始模拟数据变化...")

    while True:
        try:
            time.sleep(5)  # 每5秒更新一次

            # 随机切换单点信息
            if random.random() > 0.5:
                ioa = random.choice([1, 2])
                value = bool(random.randint(0, 1))
                server.update_data_point('single', ioa, value)
                print(f"更新单点信息 IOA={ioa}, Value={value}")

            # 随机更新双点信息
            if random.random() > 0.7:
                ioa = 100
                value = random.randint(1, 2)  # 1=分, 2=合
                server.update_data_point('double', ioa, value)
                print(f"更新双点信息 IOA={ioa}, Value={value}")

        except Exception as e:
            print(f"模拟数据错误: {e}")
            break


def main():
    """主函数"""
    print("=" * 70)
    print("IEC60870-5-104 Slave测试服务器 - 示例程序")
    print("=" * 70)

    # 创建服务器
    server = IEC104SlaveServer('config.json')

    # 启动服务器
    server.start()

    print("\n服务器已启动")
    print(f"监听地址: {server.host}:{server.port}")
    print(f"公共地址: {server.config['station']['common_address']}")
    print("\n数据点配置:")
    print(f"  - 单点信息: {len(server.data_manager.single_points)} 个")
    print(f"  - 双点信息: {len(server.data_manager.double_points)} 个")
    print(f"  - 归一化测量值: {len(server.data_manager.normalized_values)} 个")
    print(f"  - 标度化测量值: {len(server.data_manager.scaled_values)} 个")
    print(f"  - 短浮点测量值: {len(server.data_manager.float_values)} 个")

    # 启动数据变化模拟线程
    sim_thread = threading.Thread(target=simulate_data_changes, args=(server,), daemon=True)
    sim_thread.start()

    print("\n" + "=" * 70)
    print("服务器正在运行...")
    print("连接信息:")
    print("  - 可以使用IEC104客户端连接到此服务器")
    print("  - 支持总召唤、单点命令、双点命令等")
    print("  - 数据点会每5秒随机变化")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 70)

    try:
        # 保持运行，定期显示状态
        while True:
            time.sleep(10)
            conn_count = server.get_active_connections_count()
            if conn_count > 0:
                print(f"\n当前活动连接数: {conn_count}")

    except KeyboardInterrupt:
        print("\n\n收到停止信号，正在关闭服务器...")
    finally:
        server.stop()
        print("服务器已停止")
        print("再见!")


if __name__ == '__main__':
    main()
