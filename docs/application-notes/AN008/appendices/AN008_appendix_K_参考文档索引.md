# 附录 K：参考文档索引

> 本附录汇总 AN008 PMBus 应用手册引用和参考的所有文档，按类别排列。

---

## K.1 PMBus / SMBus / I²C 规范

| 文档名称 | 版本 | 发布组织 | 说明 | 在线获取 |
|---------|------|---------|------|---------|
| PMBus Power Management Protocol Specification, Part I — Transport | Rev 1.2 / Rev 1.3.1 | SM-IF | PMBus 传输层规范，定义物理层和数据链路层要求（基于 SMBus） | [smbus.org](https://smbus.org/specs/) |
| PMBus Power Management Protocol Specification, Part II — Command Language | Rev 1.2 / Rev 1.3.1 | SM-IF | PMBus 命令集规范，定义所有标准命令、数据格式和设备行为 | [smbus.org](https://smbus.org/specs/) |
| System Management Bus (SMBus) Specification | v3.0 / v3.1 | SBS-IF / Intel | SMBus 规范，定义电气特性、时序参数和传输协议 | [smbus.org](https://smbus.org/specs/) |
| I²C-bus Specification | v6.0 / v7.0 | NXP | I²C 总线规范，PMBus/SMBus 物理层的基础参考 | [nxp.com](https://www.nxp.com/docs/en/user-guide/UM10204.pdf) |

## K.2 Omnion Power 产品文档

| 文档名称 | 说明 |
|---------|------|
| 各产品 Datasheet | 各 Omnion Power 数字电源产品的完整电气规格、PMBus 命令支持列表、默认值和范围。以具体产品型号为准 |
| AN008 PMBus 应用手册 | 本手册，PMBus 接口使用指南（您正在阅读的文档） |

## K.3 技术参考资料

| 文档名称 | 说明 |
|---------|------|
| PMBus Revision 1.2 vs 1.3.1 对比报告 | PMBus 版本差异参考，了解协议演进方向 |
| PMBus 问题案例报告 | 常见 PMBus 通信问题与解决方案汇编 |
| Omnion Power PMBus Interface Reference | Omnion Power PMBus 命令接口参考文档（通用模板） |

## K.4 编程与开发工具

| 工具 / 库 | 说明 | 获取方式 |
|----------|------|---------|
| Python smbus2 | Python SMBus/I²C 库，用于 Linux 上的 PMBus 通信开发 | `pip install smbus2` |
| Python smbus | Python SMBus 库（smbus2 的前身） | `pip install smbus` |
| i2c-tools | Linux I²C 工具集（i2cdetect, i2cget, i2cset, i2cdump） | 各 Linux 发行版软件包管理器 |
| USB-to-I2C/SMBus 适配器 | 用于 PC 端 PMBus 通信调试的硬件适配器 | 参见适配器厂商文档 |

## K.5 调试工具

| 工具类型 | 说明 | 典型应用 |
|---------|------|---------|
| 数字示波器 | 用于观测 SCL/SDA/SMBALERT# 信号波形、时序参数测量 | 总线时序调试、Clock Stretching 验证 |
| 逻辑分析仪 | 用于长时间抓取 PMBus 事务、协议解码和分析 | 通信协议调试、数据完整性验证 |
| I²C/SMBus 协议解码器 | 逻辑分析仪的解码模块，自动识别 PMBus 事务类型 | 事务级调试 |

## K.6 推荐阅读顺序

针对不同背景的读者，建议的阅读顺序如下：

**PMBus 初学者（系统工程师 / FAE）**

1. 第 1 章（引言）→ 第 2 章（协议基础）→ 第 3 章（硬件接口设计）→ 第 4 章（传输协议）
2. 第 5 章（数据格式）→ 第 6 章（PEC）→ 第 8 章（状态监控与故障管理）
3. 第 9 章（控制与配置）→ 第 12 章（遥测）→ 第 7 章（SMBALERT）
4. 附录 B（Linear 快速参考）→ 附录 I（FAQ）

**固件工程师（已有 PMBus 基础）**

1. 第 4 章（传输协议）→ 第 5 章（数据格式）→ 第 6 章（PEC）
2. 第 8 章（状态监控与故障管理）→ 第 9 章（控制与配置）
3. 第 14 章（主机端驱动开发指南）→ 第 16 章（Python 编程示例）
4. 附录 A（命令列表）→ 附录 D/E（STATUS/FAULT_RESPONSE 位域）

**快速上手（仅需基本操作）**

1. 第 3 章（硬件接口设计）→ 第 9 章（ON/OFF 控制）→ 第 12 章（遥测）
2. 第 16 章（Python 编程示例）
3. 附录 A（命令列表）→ 附录 B（Linear 快速参考）

---

> **提示**: 本手册涉及的协议细节均以 PMBus Specification Rev 1.2 和 SMBus Specification v3.0 为准。建议开发者在条件允许时查阅规范原文以获取最权威的信息。
