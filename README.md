# IEC60870-5-104 Slave测试框架

一个全面的IEC60870-5-104规约Slave（从站）测试框架，用于测试104从站设备的链路健壮性、协议一致性、性能和压力承受能力。

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 项目特点

### 测试框架特性

- ✅ **链路健壮性测试** - 连接管理、重连、超时、异常断开等
- ✅ **协议一致性测试** - 帧格式、序号管理、总召唤流程等
- ✅ **性能测试** - 响应时间、吞吐量、并发处理等
- ✅ **压力测试** - 极限连接数、洪水攻击、畸形数据等
- 📊 **测试报告** - HTML和JSON格式的详细测试报告
- 🔧 **灵活配置** - 可自定义测试参数和场景
- 📝 **详细日志** - 完整的测试过程记录

### 包含的Slave实现

项目还包含一个功能完整的IEC104 Slave服务器实现，可用于：
- 测试框架的验证目标
- 学习IEC104协议
- 开发原型参考

## 📁 项目结构

```
IEC60870-5-Test/
├── test_framework/          # 测试框架核心
│   ├── __init__.py
│   ├── base_test.py        # 测试基类
│   ├── iec104_client.py    # 测试客户端
│   ├── link_test.py        # 链路健壮性测试
│   ├── protocol_test.py    # 协议一致性测试
│   ├── performance_test.py # 性能测试
│   └── stress_test.py      # 压力测试
├── iec104/                  # IEC104协议实现
│   ├── constants.py        # 协议常量
│   ├── apci.py            # APCI实现
│   └── asdu.py            # ASDU实现
├── slave_server.py         # Slave服务器
├── connection_handler.py   # 连接处理
├── data_manager.py         # 数据点管理
├── run_tests.py           # 测试运行器
├── config.json            # 配置文件
├── TEST_GUIDE.md          # 详细测试指南
└── README.md              # 本文件
```

## 🚀 快速开始

### 基本测试流程

#### 1. 启动Slave服务器

```bash
# 启动内置的Slave服务器（用于测试）
python slave_server.py
```

#### 2. 运行测试

```bash
# 运行所有测试
python run_tests.py

# 运行特定测试套件
python run_tests.py --test link           # 链路测试
python run_tests.py --test protocol       # 协议测试
python run_tests.py --test performance    # 性能测试
python run_tests.py --test stress         # 压力测试
```

#### 3. 查看测试报告

```bash
# 生成HTML和JSON报告
python run_tests.py --html-report report.html --json-report report.json

# 在浏览器中打开
# Windows: start report.html
# Linux: xdg-open report.html
# Mac: open report.html
```

### 测试外部Slave设备

```bash
# 指定目标设备的IP和端口
python run_tests.py --host 192.168.1.100 --port 2404

# 使用配置文件
python run_tests.py --host 192.168.1.100 --config config.json --html-report report.html
```

## 📊 测试套件详解

### 1. 链路健壮性测试 (10个测试用例)

测试连接管理和异常处理能力：

- 基本连接建立和断开
- STARTDT/STOPDT/TESTFR机制
- 重连能力和超时处理
- 突然断开和异常场景
- 空闲超时和心跳机制

**关键指标:**
- 连接成功率 > 99%
- 重连能力验证
- TESTFR响应正确性

### 2. 协议一致性测试 (10个测试用例)

验证IEC104协议标准符合性：

- APCI帧格式验证
- 序号连续性检查
- 总召唤流程完整性
- 传送原因(COT)正确性
- 公共地址匹配
- 无效帧处理

**关键指标:**
- 帧格式100%符合标准
- 序号管理无错误
- 总召唤流程完整

### 3. 性能测试 (8个测试用例)

评估关键性能指标：

- 连接建立时间
- TESTFR响应时间
- 总召唤完成时间
- 数据吞吐量
- 序号处理速度
- 内存泄漏检测

**性能基准:**
- 连接建立: < 500ms
- TESTFR响应: < 100ms
- 总召唤: < 3s
- 无内存泄漏

### 4. 压力测试 (10个测试用例)

验证极限场景下的稳定性：

- 最大连接数测试
- 快速连接/断开循环
- 帧洪水攻击
- 畸形数据注入
- 并发操作
- 长时间连接稳定性

**压力指标:**
- 最大连接数达标
- 快速连接成功率 > 95%
- 抵御洪水攻击
- 长时间连接稳定

## 📈 测试报告示例

### 控制台输出

```
==============================================================================
IEC60870-5-104 Slave测试框架
==============================================================================
测试目标: 127.0.0.1:2404
开始时间: 2026-02-09 10:30:00
==============================================================================

==============================================================================
执行测试套件: 链路健壮性测试
==============================================================================
[✓] test_basic_connection - 通过 (0.15s)
[✓] test_startdt_stopdt - 通过 (0.32s)
[✓] test_testfr_mechanism - 通过 (0.18s)
...

测试总结
==============================================================================
总测试数: 38
✓ 通过: 35 (92.1%)
✗ 失败: 2 (5.3%)
! 错误: 1 (2.6%)

总耗时: 45.23秒
==============================================================================
```

### HTML报告

生成的HTML报告包含：
- 可视化的测试统计
- 每个测试用例的详细结果
- 性能数据图表
- 失败原因分析

## 🔧 配置说明

### config.json

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 2404,
    "max_connections": 5
  },
  "station": {
    "common_address": 1,
    "cot_size": 2,
    "asdu_address_size": 2,
    "ioa_size": 3
  }
}
```

## 💡 使用场景

### 1. 设备验收测试

在采购IEC104设备时，使用本框架进行验收测试：

```bash
# 全面测试
python run_tests.py --host <设备IP> --port 2404 \
    --html-report acceptance_report.html

# 检查报告确认设备符合要求
```

### 2. 协议开发验证

开发IEC104 Slave时，使用测试框架验证：

```bash
# 开发过程中持续测试
python run_tests.py --test protocol  # 协议符合性
python run_tests.py --test link      # 链路稳定性

# 发布前完整测试
python run_tests.py --html-report dev_test.html
```

### 3. 性能基准测试

建立性能基线并进行回归测试：

```bash
# 性能基准测试
python run_tests.py --test performance --json-report baseline.json

# 定期回归测试
python run_tests.py --test performance --json-report regression.json
# 对比baseline.json和regression.json
```

### 4. 压力测试

上线前验证系统承载能力：

```bash
python run_tests.py --test stress --html-report stress_report.html
```

## 🛠️ 高级功能

### 编程方式使用

```python
from test_framework import LinkRobustnessTest, PerformanceTest

# 创建测试实例
link_test = LinkRobustnessTest('192.168.1.100', 2404)
perf_test = PerformanceTest('192.168.1.100', 2404)

# 运行测试
link_results = link_test.run_all()
perf_results = perf_test.run_all()

# 分析结果
for result in link_results:
    print(f"{result.test_name}: {result.status.value}")
    print(f"  耗时: {result.duration:.2f}s")
    print(f"  详情: {result.details}")
```

### 自定义测试用例

```python
from test_framework import BaseTest, TestResult

class MyCustomTest(BaseTest):
    """自定义测试"""
    
    def test_my_scenario(self, result: TestResult):
        """测试特定场景"""
        from test_framework.iec104_client import IEC104TestClient
        
        client = IEC104TestClient(self.slave_host, self.slave_port)
        try:
            client.connect()
            # 自定义测试逻辑
            client.send_testfr()
            frame = client.wait_for_frame(timeout=2.0)
            
            self.assert_true(frame is not None, "未收到响应")
            result.details['response_received'] = True
        finally:
            client.disconnect()
```

## 📚 文档

- [TEST_GUIDE.md](TEST_GUIDE.md) - 详细测试指南
- [QUICKSTART.md](QUICKSTART.md) - 快速开始（Slave服务器）
- 代码注释 - 完整的API文档

## 🔍 故障排除

### 常见问题

**1. 连接失败**
```bash
# 检查目标服务器是否运行
ping <目标IP>

# 检查端口是否开放
telnet <目标IP> 2404
```

**2. 测试超时**
- 检查网络延迟
- 增加超时时间（修改代码中的timeout参数）
- 查看Slave设备日志

**3. 大量测试失败**
- 确认配置参数匹配（公共地址、ASDU大小等）
- 查看具体失败的测试用例
- 启用DEBUG日志查看详细过程

## 🎓 学习资源

- [IEC 60870-5-104标准文档](https://webstore.iec.ch/)
- [协议解析工具推荐](https://www.wireshark.org/)
- 示例代码：查看`test_framework/`目录

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目仅供学习和测试使用。

## 📞 联系方式

如有问题或建议，请通过Issue反馈。

---

**注意**: 本测试框架设计用于测试IEC104 Slave设备。在生产环境使用前请充分测试。
