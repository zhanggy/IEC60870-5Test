# IEC60870-5-104 Slave测试框架 - 快速入门

## 5分钟快速开始

### 第一步：启动服务器

**Windows:**
```bash
# 双击运行
start_server.bat

# 或在命令行中
python slave_server.py
```

**Linux/Mac:**
```bash
chmod +x start_server.sh
./start_server.sh

# 或直接运行
python3 slave_server.py
```

你应该看到：
```
======================================================================
IEC60870-5-104 Slave测试服务器
======================================================================
监听地址: 0.0.0.0:2404
服务器正在运行，按 Ctrl+C 停止
======================================================================
```

### 第二步：测试连接

打开新的终端窗口，运行测试客户端：

```bash
python test_client.py
```

你应该看到客户端执行以下操作：
1. 连接到服务器
2. 发送STARTDT激活
3. 发送测试帧
4. 发送总召唤
5. 接收数据点信息
6. 发送STOPDT

### 第三步：运行带数据模拟的示例

```bash
python example.py
```

这将启动服务器并每5秒随机更新数据点值。

## 使用自己的IEC104客户端

可以使用任何IEC104客户端工具连接到服务器：

- **主机**: 127.0.0.1 (本地) 或服务器IP地址
- **端口**: 2404
- **公共地址**: 1
- **ASDU地址大小**: 2字节
- **IOA地址大小**: 3字节
- **传送原因大小**: 2字节

## 配置数据点

编辑 `config.json`:

```json
{
  "data_points": {
    "single_point": [
      {"ioa": 1, "value": false, "quality": 0},
      {"ioa": 2, "value": true, "quality": 0}
    ],
    "measured_float": [
      {"ioa": 3000, "value": 123.45, "quality": 0}
    ]
  }
}
```

重启服务器使配置生效。

## 编程使用

```python
from slave_server import IEC104SlaveServer

# 创建服务器
server = IEC104SlaveServer('config.json')
server.start()

# 更新数据点
server.update_data_point('single', ioa=1, value=True)

# 获取数据点
value, quality = server.get_data_point('single', ioa=1)
print(f"值: {value}, 品质: {quality}")

# 停止服务器
server.stop()
```

## 运行测试

```bash
python tests.py
```

## 常见问题

### 端口被占用
修改 `config.json` 中的端口：
```json
{
  "server": {
    "port": 2405
  }
}
```

### 防火墙问题
确保端口2404（或你配置的端口）在防火墙中允许。

### Python版本
需要Python 3.6或更高版本。

## 下一步

- 阅读完整的 [README.md](README.md) 了解详细功能
- 查看 [example.py](example.py) 学习高级用法
- 修改 [config.json](config.json) 配置你的数据点
- 查看 [tests.py](tests.py) 了解单元测试

## 支持的命令

当前实现支持：

✅ **连接管理**
- STARTDT/STOPDT - 启动/停止数据传输
- TESTFR - 测试帧

✅ **数据采集**
- C_IC_NA_1 - 总召唤
- C_RD_NA_1 - 读命令

✅ **控制命令**
- C_SC_NA_1 - 单点命令
- C_DC_NA_1 - 双点命令

✅ **数据类型**
- 单点信息、双点信息
- 归一化值、标度化值、短浮点值
- 步位置信息

需要其他功能？查看代码即可轻松扩展！

---
**提示**: 首次使用建议先运行 `python tests.py` 确保一切正常。
