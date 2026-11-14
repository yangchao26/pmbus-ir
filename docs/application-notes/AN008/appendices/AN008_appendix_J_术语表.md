# 附录 J：术语表

> 本附录汇总 AN008 全手册使用的术语与缩写，按主题分类排列。首次出现的章节以括号标注。

---

## J.1 协议与标准

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| PMBus | Power Management Bus | 电源管理总线协议，由 SM-IF 制定，在 SMBus 上定义电源管理命令集 | 第 1 章 |
| SMBus | System Management Bus | 系统管理总线，I²C 的受限超集，增加时序约束和电气要求 | 第 2 章 |
| I²C | Inter-Integrated Circuit | 内部集成电路总线，由 Philips (NXP) 制定，PMBus/SMBus 的物理层基础 | 第 2 章 |
| SM-IF | System Management Interface Forum | PMBus 规范的制定和维护组织 | 第 1 章 |
| ARA | Alert Response Address | 告警响应地址（0x0C），主机读取该地址以识别报警设备 | 第 7 章 |
| ARP | Address Resolution Protocol | SMBus 地址解析协议（Omnion Power 模块不支持） | 第 1 章 |
| GROUP | Group Protocol | PMBus 多设备同时寻址协议（Omnion Power 模块不支持） | 第 1 章 |

## J.2 总线信号

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| SCL | Serial Clock Line | 串行时钟线，主机驱动，支持 Clock Stretching | 第 2 章 |
| SDA | Serial Data Line | 串行数据线，双向传输，开漏结构 | 第 2 章 |
| SMBALERT# | SMBus Alert | SMBus 告警信号，开漏输出，低电平有效，用于从设备向主机报告故障 | 第 7 章 |
| CTRL | Control | PMBus 控制信号（可选），用于设备使能控制 | 第 3 章 |
| WP | Write Protect | 写保护信号（可选），用于防止意外修改配置 | 第 3 章 |
| PGOOD | Power Good | 电源正常指示信号，输出电压在规定范围内时有效 | 第 9 章 |
| R/W# | Read/Write Bit | 地址字节中的读/写方向位，1 = 读，0 = 写 | 第 2 章 |

## J.3 总线事务与协议机制

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| ACK | Acknowledge | 确认信号，接收方在每字节后拉低 SDA 表示确认 | 第 2 章 |
| NACK | Not Acknowledge | 非确认信号，接收方释放 SDA 表示未确认 | 第 2 章 |
| START (S) | Start Condition | 起始条件，SCL 为高时 SDA 产生下降沿 | 第 2 章 |
| STOP (P) | Stop Condition | 停止条件，SCL 为高时 SDA 产生上升沿 | 第 2 章 |
| Sr | Repeated Start | 重复起始条件，不释放总线的情况下重新发起传输 | 第 4 章 |
| Clock Stretching | — | 时钟拉伸，从设备拉低 SCL 以延长处理时间 | 第 2 章 |
| Bus Timeout | — | 总线超时，SMBus 规定的超时机制（25 ms ~ 35 ms），用于检测总线挂死 | 第 2 章 |
| Bus Recovery | — | 总线恢复，主机发送额外 SCL 时钟脉冲以恢复被锁死的总线 | 第 2 章 |
| Arbitration | — | 总线仲裁，多主机同时访问时通过 SDA 线与逻辑决定优先级 | 第 2 章 |
| Open-Drain | — | 开漏输出，SDA/SMBALERT# 等信号的输出结构，需要外部上拉电阻 | 第 2 章 |
| Wired-OR | — | 线或连接，多个开漏输出信号通过上拉电阻连接到同一信号线 | 第 7 章 |

## J.4 PMBus 事务类型

| 术语 / 缩写 | 说明 | 首次出现 |
|-------------|------|---------|
| Send Byte | 无数据的单命令事务，仅发送地址+W + 命令字节 | 第 4 章 |
| Receive Byte | 无命令码的单字节读取，仅发送地址+R 后读取一字节 | 第 4 章 |
| Write Byte | 写单字节：地址+W → 命令 → 数据 → STOP | 第 4 章 |
| Read Byte | 读单字节：地址+W → 命令 → Sr → 地址+R → 数据 → NACK → STOP | 第 4 章 |
| Write Word | 写双字节：地址+W → 命令 → 低字节 → 高字节 → STOP | 第 4 章 |
| Read Word | 读双字节：地址+W → 命令 → Sr → 地址+R → 低字节 → 高字节 → NACK → STOP | 第 4 章 |
| Block Write | 块写：地址+W → 命令 → 字节计数 N → N 字节数据 → STOP | 第 4 章 |
| Block Read | 块读：地址+W → 命令 → Sr → 地址+R → 字节计数 N → N 字节数据 → NACK → STOP | 第 4 章 |
| Process Call | 双向数据传输：写 2 字节后立即读 2 字节 | 第 4 章 |

## J.5 数据格式

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| Linear 格式 | Linear Format | PMBus 数值数据编码方式，5-bit 指数 N + 11-bit 尾数 Y：Value = Y × 2^N | 第 5 章 |
| Direct 格式 | Direct Format | PMBus 数值数据编码方式，参数 m、b、R：Value = (Y × m + b) × 10^R（Omnion Power 不支持） | 第 5 章 |
| ULINEAR16 | Unsigned Linear 16-bit | 无符号 16-bit Linear 格式，用于电压数据（VOUT_MODE 提供指数 N） | 第 5 章 |
| VOUT_MODE | — | 输出电压数据格式命令，定义 VOUT 相关命令使用的固定指数 N | 第 5 章 |
| Two's Complement | 二进制补码 | 有符号整数的编码方式，用于 Linear 格式的指数和尾数 | 第 5 章 |
| LSB | Least Significant Byte/Bit | 最低有效字节/位；PMBus 多字节数据低字节先传（Little-Endian） | 第 2 章 |
| MSB | Most Significant Byte/Bit | 最高有效字节/位 | 第 2 章 |
| Mantissa | 尾数 | Linear 格式中的有效数值部分（Y） | 第 5 章 |
| Exponent | 指数 | Linear 格式中的缩放因子（N） | 第 5 章 |

## J.6 错误检测与校验

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| PEC | Packet Error Check | 包错误校验，基于 CRC-8 的校验码，附加在每个事务末尾以确保数据完整性 | 第 6 章 |
| CRC-8 | Cyclic Redundancy Check 8-bit | 8 位循环冗余校验，多项式 C(x) = x⁸ + x² + x + 1 (0x07) | 第 6 章 |

## J.7 设备与存储

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| Host / Master | 主机 / 主设备 | 通过 PMBus 发送命令的控制器，通常是 BMC、MCU 或 FPGA | 第 1 章 |
| Slave / Device | 从设备 | 响应 PMBus 命令的电源模块 | 第 1 章 |
| NVM | Non-Volatile Memory | 非易失性存储器，掉电后数据不丢失 | 第 10 章 |
| EEPROM | Electrically Erasable Programmable ROM | 电可擦除可编程只读存储器 | 第 10 章 |
| Operating Memory | — | 运行时配置存储（RAM），掉电后丢失 | 第 10 章 |
| Default Store | — | 默认参数存储（NVM），通过 STORE_DEFAULT_ALL 写入 | 第 10 章 |
| User Store | — | 用户自定义参数存储（NVM，如支持） | 第 10 章 |

## J.8 状态与故障

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| FAULT | Fault | 故障，触发保护动作（关断、重启等） | 第 8 章 |
| WARNING | Warning | 警告，记录状态但不触发保护动作 | 第 8 章 |
| FAULT_RESPONSE | Fault Response | 故障响应配置，定义故障发生后的行为 | 第 8 章 |
| FAULT_LIMIT | Fault Limit | 故障阈值，超过该值触发故障保护 | 第 8 章 |
| WARN_LIMIT | Warning Limit | 警告阈值，超过该值记录警告状态 | 第 8 章 |
| OVP | Over Voltage Protection | 输出过压保护 | 第 8 章 |
| UVP | Under Voltage Protection | 输出欠压保护 | 第 8 章 |
| OCP | Over Current Protection | 输出过流保护 | 第 8 章 |
| OTP | Over Temperature Protection | 过温保护 | 第 8 章 |
| UTP | Under Temperature Protection | 欠温保护 | 第 8 章 |
| CLEAR_FAULTS | — | 清除故障命令，清除锁存的故障状态并释放 SMBALERT# | 第 8 章 |

## J.9 控制与配置

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| OPERATION | — | 操作命令，控制模块 ON/OFF 和裕量模式 | 第 9 章 |
| ON_OFF_CONFIG | — | ON/OFF 配置命令，定义硬件引脚行为和极性 | 第 9 章 |
| WRITE_PROTECT | — | 写保护命令，控制参数是否可修改 | 第 9 章 |
| PAGE | — | 页面选择命令，用于多路输出模块选择目标通道 | 第 9 章 |
| Margin High | — | 裕量高调节，将输出电压暂时偏移至高于标称值 | 第 9 章 |
| Margin Low | — | 裕量低调节，将输出电压暂时偏移至低于标称值 | 第 9 章 |
| Telemetry | — | 遥测数据，实时监测量（电压、电流、温度、功率等） | 第 12 章 |

## J.10 产品与行业

| 术语 / 缩写 | 全称 | 说明 | 首次出现 |
|-------------|------|------|---------|
| DC-DC | Direct Current to Direct Current | 直流到直流变换器 | 第 1 章 |
| IBC | Intermediate Bus Converter | 中间母线变换器 | 第 1 章 |
| POL | Point-of-Load | 负载点电源模块 | 第 1 章 |
| PSU | Power Supply Unit | 电源供应单元 | 第 1 章 |
| BMC | Baseboard Management Controller | 基板管理控制器（常见于服务器，作为 PMBus 主机） | 第 1 章 |
| FAE | Field Application Engineer | 现场应用工程师 | 第 1 章 |
| Datasheet | — | 数据手册，产品电气规格和功能描述文档 | 第 1 章 |
| MFR | Manufacturer | 制造商（用于 MFR_xxx 命令前缀） | 第 11 章 |
