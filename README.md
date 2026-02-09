# IEC60870-5-101/104 测试工具

基于IEC60870-5-101/104规约的测试工具，支持串口（101）和TCP/IP（104）两种通信方式。

## 功能特性

- ✅ IEC60870-5-104 协议支持（TCP/IP）
  - 客户端和服务器模式
  - APDU（应用规约数据单元）处理
  - 常用ASDU（应用服务数据单元）支持
  - STARTDT/STOPDT/TESTFR控制帧
  - 总召唤命令

- ✅ IEC60870-5-101 协议支持（串口）
  - FT1.2帧格式
  - 串口通信管理
  - 总召唤命令

- ✅ 命令行工具
  - 灵活的参数配置
  - 支持客户端和服务器模式
  - 详细的日志输出

## 安装

### 从源码安装

```bash
git clone https://github.com/zhanggy/IEC60870-5Test.git
cd IEC60870-5Test
pip install -r requirements.txt
python setup.py install
```

### 开发模式安装

```bash
pip install -e .
```

## 使用方法

### 命令行工具

#### IEC104 客户端

连接到IEC104服务器并发送总召唤命令：

```bash
iec60870-test iec104-client --host 192.168.1.100 --port 2404 --interrogation
```

启用测试帧和详细日志：

```bash
iec60870-test iec104-client --host 192.168.1.100 --testfr --interrogation -v
```

自定义监控时长：

```bash
iec60870-test iec104-client --host 192.168.1.100 --duration 60 --interrogation
```

#### IEC104 服务器

启动IEC104服务器：

```bash
iec60870-test iec104-server --host 0.0.0.0 --port 2404
```

#### IEC101 客户端

通过串口连接（Linux）：

```bash
iec60870-test iec101-client --port /dev/ttyUSB0 --baudrate 9600 --interrogation
```

通过串口连接（Windows）：

```bash
iec60870-test iec101-client --port COM1 --baudrate 9600 --interrogation
```

自定义串口参数：

```bash
iec60870-test iec101-client --port /dev/ttyUSB0 --baudrate 19200 --parity E --stopbits 1
```

### Python API

#### IEC104 客户端示例

```python
from iec60870.protocol.iec104 import IEC104Client
import time

# 创建客户端
client = IEC104Client('192.168.1.100', 2404)

# 设置数据回调
def on_data(asdu):
    print(f"收到数据: Type={asdu.type_id}, COT={asdu.cot}")

client.set_data_callback(on_data)

# 连接
if client.connect():
    # 启动数据传输
    client.send_startdt()
    time.sleep(1)
    
    # 发送总召唤
    client.send_interrogation(ca_address=1)
    time.sleep(5)
    
    # 断开连接
    client.disconnect()
```

#### IEC104 服务器示例

```python
from iec60870.protocol.iec104 import IEC104Server
import time

# 创建服务器
server = IEC104Server('0.0.0.0', 2404)

# 启动服务器
if server.start():
    print("服务器已启动")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
```

#### IEC101 客户端示例

```python
from iec60870.protocol.iec101 import IEC101Client
import time

# 创建客户端
client = IEC101Client(port='/dev/ttyUSB0', baudrate=9600)

# 设置数据回调
def on_data(data):
    print(f"收到数据: {data.hex()}")

client.set_data_callback(on_data)

# 连接
if client.connect():
    # 发送总召唤
    client.send_interrogation(ca_address=1)
    time.sleep(5)
    
    # 断开连接
    client.disconnect()
```

## 示例程序

在 `examples/` 目录中提供了完整的示例程序：

- `iec104_client_example.py` - IEC104客户端完整示例
- `iec104_server_example.py` - IEC104服务器完整示例
- `iec101_client_example.py` - IEC101客户端完整示例

运行示例：

```bash
python examples/iec104_client_example.py
python examples/iec104_server_example.py
python examples/iec101_client_example.py
```

## 项目结构

```
IEC60870-5Test/
├── iec60870/              # 主包
│   ├── __init__.py
│   ├── cli.py            # 命令行接口
│   └── protocol/         # 协议实现
│       ├── __init__.py   # 通用定义
│       ├── iec104.py     # IEC104协议实现
│       └── iec101.py     # IEC101协议实现
├── examples/             # 示例程序
│   ├── iec104_client_example.py
│   ├── iec104_server_example.py
│   └── iec101_client_example.py
├── requirements.txt      # 依赖包
├── setup.py             # 安装脚本
├── README.md            # 说明文档
└── LICENSE              # MIT许可证
```

## 协议支持

### IEC60870-5-104 (TCP/IP)

- APCI格式：
  - I-format（信息传输）
  - S-format（监视功能）
  - U-format（无编号控制）

- 控制命令：
  - STARTDT（启动数据传输）
  - STOPDT（停止数据传输）
  - TESTFR（测试帧）

- ASDU类型：
  - C_IC_NA_1 (100) - 总召唤命令
  - 支持扩展其他ASDU类型

### IEC60870-5-101 (Serial)

- FT1.2帧格式：
  - 固定长度帧
  - 可变长度帧

- 控制功能：
  - 复位链路
  - 用户数据传输
  - 总召唤命令

## 技术规范

- 符合IEC60870-5-101标准（串口通信）
- 符合IEC60870-5-104标准（TCP/IP通信）
- Python 3.6+
- 支持Linux和Windows平台

## 常见问题

### Q: 如何测试IEC104协议？

A: 可以在本地启动服务器和客户端进行测试：

```bash
# 终端1：启动服务器
iec60870-test iec104-server

# 终端2：启动客户端
iec60870-test iec104-client --host 127.0.0.1 --interrogation
```

### Q: IEC101需要什么硬件？

A: 需要串口设备或USB转串口适配器。在Linux上需要适当的权限访问串口设备：

```bash
sudo usermod -a -G dialout $USER  # 添加用户到dialout组
# 或临时使用
sudo chmod 666 /dev/ttyUSB0
```

### Q: 如何查看详细的协议交互？

A: 使用 `-v` 或 `--verbose` 参数启用详细日志：

```bash
iec60870-test iec104-client --host 192.168.1.100 -v
```

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e .

# 运行示例
python examples/iec104_client_example.py
```

### 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

zhanggy

## 参考资料

- IEC 60870-5-101: Transmission protocols - Companion standard for basic telecontrol tasks
- IEC 60870-5-104: Network access for IEC 60870-5-101 using standard transport profiles
