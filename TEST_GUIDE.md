# IEC60870-5-104 Slave测试框架使用指南

## 概述

这是一个全面的IEC60870-5-104 Slave设备测试框架，包含链路健壮性、协议一致性、性能和压力测试。

## 快速开始

### 1. 启动被测Slave服务器

```bash
# 在一个终端窗口启动Slave服务器
python slave_server.py
```

### 2. 运行测试

```bash
# 运行所有测试
python run_tests.py

# 运行特定类型的测试
python run_tests.py --test link           # 链路健壮性测试
python run_tests.py --test protocol       # 协议一致性测试
python run_tests.py --test performance    # 性能测试
python run_tests.py --test stress         # 压力测试

# 指定目标服务器
python run_tests.py --host 192.168.1.100 --port 2404

# 生成测试报告
python run_tests.py --html-report report.html --json-report report.json
```

## 测试套件说明

### 1. 链路健壮性测试 (LinkRobustnessTest)

测试连接管理和链路稳定性。

**测试用例:**
- `test_basic_connection` - 基本连接测试
- `test_startdt_stopdt` - 启动/停止数据传输测试
- `test_testfr_mechanism` - 测试帧机制
- `test_reconnection` - 重连能力测试
- `test_connection_timeout` - 连接超时测试
- `test_abrupt_disconnection` - 突然断开连接测试
- `test_multiple_startdt` - 多次STARTDT测试
- `test_data_transfer_without_startdt` - 未启动数据传输时发送数据
- `test_idle_timeout_testfr` - 空闲超时TESTFR机制
- `test_socket_error_handling` - Socket错误处理

**关注点:**
- 连接建立和断开的正确性
- STARTDT/STOPDT/TESTFR机制
- 异常情况处理
- 重连能力

### 2. 协议一致性测试 (ProtocolComplianceTest)

测试协议格式和标准符合性。

**测试用例:**
- `test_apci_start_byte` - APCI起始字节验证
- `test_sequence_number_management` - 序号管理测试
- `test_general_interrogation_response` - 总召唤响应测试
- `test_invalid_frame_handling` - 无效帧处理
- `test_frame_length_validation` - 帧长度验证
- `test_max_sequence_number_rollover` - 序号翻转测试
- `test_u_frame_types` - U格式帧类型测试
- `test_s_frame_format` - S格式帧测试
- `test_cot_values` - 传送原因值测试
- `test_common_address` - 公共地址测试

**关注点:**
- 帧格式正确性
- 序号连续性
- 传送原因符合性
- 总召唤流程完整性

### 3. 性能测试 (PerformanceTest)

测试响应时间和吞吐量。

**测试用例:**
- `test_connection_establishment_time` - 连接建立时间
- `test_testfr_response_time` - TESTFR响应时间
- `test_general_interrogation_response_time` - 总召唤响应时间
- `test_data_throughput` - 数据吞吐量
- `test_sequence_number_performance` - 序号处理性能
- `test_concurrent_testfr` - 并发TESTFR性能
- `test_memory_leak_detection` - 内存泄漏检测
- `test_sustained_load` - 持续负载测试

**性能指标:**
- 连接建立: < 500ms
- TESTFR响应: < 100ms
- 总召唤完成: < 3s
- 序号处理: 无错误

### 4. 压力测试 (StressTest)

测试极限情况和高负载场景。

**测试用例:**
- `test_max_connections` - 最大连接数测试
- `test_rapid_connect_disconnect` - 快速连接断开测试
- `test_large_data_volume` - 大数据量测试
- `test_continuous_testfr_flood` - TESTFR洪水测试
- `test_malformed_frame_flood` - 畸形帧洪水测试
- `test_concurrent_operations` - 并发操作测试
- `test_sequence_number_stress` - 序号压力测试
- `test_long_running_connection` - 长时间连接测试
- `test_buffer_overflow_protection` - 缓冲区溢出保护

**压力场景:**
- 连接数上限
- 快速连接/断开循环
- 帧洪水攻击
- 畸形数据注入
- 长时间连接稳定性

## 测试报告

### HTML报告

包含可视化的测试结果，支持:
- 测试通过/失败统计
- 测试详情展示
- 性能指标可视化
- 错误信息汇总

生成方式:
```bash
python run_tests.py --html-report test_report.html
```

### JSON报告

机器可读的测试结果，包含:
- 测试元数据
- 详细测试结果
- 性能数据
- 错误堆栈

生成方式:
```bash
python run_tests.py --json-report test_report.json
```

## 配置文件

可以通过配置文件指定测试参数:

```json
{
  "station": {
    "common_address": 1,
    "max_connections": 5,
    "cot_size": 2,
    "asdu_address_size": 2,
    "ioa_size": 3
  }
}
```

使用配置:
```bash
python run_tests.py --config config.json
```

## 自定义测试

### 添加新测试用例

在对应的测试类中添加方法:

```python
def test_my_custom_test(self, result: TestResult):
    """我的自定义测试"""
    client = IEC104TestClient(self.slave_host, self.slave_port)
    
    try:
        client.connect()
        # 执行测试逻辑
        
        # 使用断言
        self.assert_true(condition, "错误消息")
        self.assert_equal(actual, expected, "值不匹配")
        
        # 记录详情
        result.details['key'] = 'value'
        
    finally:
        client.disconnect()
```

### 创建新测试套件

```python
from test_framework import BaseTest, TestResult

class MyCustomTest(BaseTest):
    """自定义测试套件"""
    
    def test_something(self, result: TestResult):
        # 测试实现
        pass
```

## 故障排除

### 连接失败

1. 确认Slave服务器已启动
2. 检查防火墙设置
3. 验证IP地址和端口

### 测试超时

1. 增加超时时间: `IEC104TestClient(host, port, timeout=10.0)`
2. 检查网络延迟
3. 查看Slave服务器日志

### 大量测试失败

1. 确认Slave实现符合IEC104标准
2. 检查配置参数匹配
3. 查看具体错误消息

## 最佳实践

1. **逐步测试** - 先运行链路测试，再运行其他测试
2. **查看日志** - 启用DEBUG日志了解详细过程
3. **隔离问题** - 单独运行失败的测试用例
4. **性能基线** - 建立性能指标基线用于回归测试
5. **持续集成** - 将测试集成到CI/CD流程

## 高级用法

### 编程方式运行测试

```python
from test_framework import LinkRobustnessTest

# 创建测试实例
test_suite = LinkRobustnessTest('127.0.0.1', 2404)

# 运行所有测试
results = test_suite.run_all()

# 分析结果
for result in results:
    print(f"{result.test_name}: {result.status.value}")
    if result.details:
        print(f"  详情: {result.details}")
```

### 自定义测试客户端

```python
from test_framework.iec104_client import IEC104TestClient

client = IEC104TestClient('127.0.0.1', 2404)
client.connect()

# 设置回调
def on_frame(frame):
    print(f"收到帧: {len(frame)} 字节")

client.on_frame_received = on_frame

# 发送测试命令
client.send_testfr()
```

## 测试覆盖范围

✅ **已覆盖:**
- 基本连接管理
- U/S/I格式帧
- 总召唤流程
- 序号管理
- TESTFR机制
- 错误处理
- 性能指标
- 压力场景

⚠️ **部分覆盖:**
- 时钟同步
- 文件传输
- 控制命令

❌ **未覆盖:**
- 加密通信
- 冗余链路
- 特定厂商扩展

## 支持

如有问题或建议，请通过Issue反馈。

---

**提示:** 首次使用建议先用默认Slave服务器进行测试，熟悉框架后再测试实际设备。
