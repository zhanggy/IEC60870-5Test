"""
简单的IEC104客户端测试工具
用于测试Slave服务器
"""

import socket

import time
from iec104 import APCI, ASDU, UType, TypeID, COT


class SimpleIEC104Client:
    """简单的IEC104客户端"""

    def __init__(self, host='127.0.0.1', port=2404):
        self.host = host
        self.port = port
        self.socket = None
        self.send_seq = 0
        self.recv_seq = 0

    def connect(self):
        """连接到服务器"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"已连接到 {self.host}:{self.port}")

    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
        print("已断开连接")

    def send_u_frame(self, utype):
        """发送U格式帧"""
        apci = APCI.create_u_frame(utype)
        self.socket.sendall(apci.to_bytes())
        print(f"发送: {apci}")

    def send_startdt(self):
        """发送启动数据传输"""
        self.send_u_frame(UType.STARTDT_ACT)

    def send_stopdt(self):
        """发送停止数据传输"""
        self.send_u_frame(UType.STOPDT_ACT)

    def send_testfr(self):
        """发送测试帧"""
        self.send_u_frame(UType.TESTFR_ACT)

    def send_general_interrogation(self, ca=1):
        """发送总召唤命令"""
        asdu = ASDU(TypeID.C_IC_NA_1, COT.ACT, 0, ca)
        asdu.num_objects = 1

        # 添加信息对象（IOA=0表示全站召唤）
        ioa_bytes = (0).to_bytes(3, 'little')
        qoi = 20  # 总召唤
        asdu_data = asdu.encode() + ioa_bytes + bytes([qoi])

        apci = APCI.create_i_frame(self.send_seq, self.recv_seq)
        apci.length = 4 + len(asdu_data)

        frame = apci.to_bytes() + asdu_data
        self.socket.sendall(frame)
        self.send_seq = (self.send_seq + 1) & 0x7FFF
        print("发送总召唤命令")

    def receive(self, timeout=5):
        """接收数据"""
        self.socket.settimeout(timeout)
        try:
            data = self.socket.recv(4096)
            if data:
                print(f"接收到 {len(data)} 字节数据")
                # 简单解析
                offset = 0
                while offset < len(data):
                    if data[offset] != 0x68:
                        offset += 1
                        continue

                    length = data[offset + 1]
                    frame = data[offset:offset + length + 2]

                    try:
                        apci = APCI.from_bytes(frame)
                        print(f"  {apci}")

                        # 更新接收序号
                        if apci.format_type == 0:  # I帧
                            self.recv_seq = (apci.send_seq + 1) & 0x7FFF
                    except Exception as e:
                        print(f"  解析错误: {e}")

                    offset += length + 2
        except socket.timeout:
            print("接收超时")
        except Exception as e:
            print(f"接收错误: {e}")


def main():
    """测试主函数"""
    print("=" * 60)
    print("IEC104客户端测试工具")
    print("=" * 60)

    client = SimpleIEC104Client()

    try:
        # 连接
        print("\n1. 连接到服务器...")
        client.connect()
        time.sleep(0.5)

        # 接收可能的连接响应
        client.receive(timeout=1)

        # 发送STARTDT
        print("\n2. 发送STARTDT激活...")
        client.send_startdt()
        time.sleep(0.5)
        client.receive()

        # 发送TESTFR
        print("\n3. 发送测试帧...")
        client.send_testfr()
        time.sleep(0.5)
        client.receive()

        # 发送总召唤
        print("\n4. 发送总召唤...")
        client.send_general_interrogation()
        time.sleep(1)

        # 接收总召唤响应
        print("\n5. 接收总召唤响应...")
        for i in range(5):
            client.receive(timeout=2)
            time.sleep(0.5)

        # 发送STOPDT
        print("\n6. 发送STOPDT...")
        client.send_stopdt()
        time.sleep(0.5)
        client.receive()

        print("\n测试完成!")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        client.disconnect()


if __name__ == '__main__':
    main()
