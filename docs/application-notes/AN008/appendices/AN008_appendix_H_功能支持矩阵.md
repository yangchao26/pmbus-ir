# 附录 H 功能支持矩阵

> 本附录以矩阵形式汇总 Omnion Power 数字电源模块的 PMBus 功能支持情况，涵盖协议层功能、命令类别、数据格式、不支持的功能列表以及可选功能说明。本附录为通用参考，具体参数以各产品 Datasheet 为准。

---

## H.1 协议层功能支持矩阵

### H.1.1 PMBus/SMBus/I2C 协议特性

| 功能 | 支持 | 备注 |
|------|------|------|
| PMBus 规范版本 Rev 1.2 (Part I & Part II) | 支持 | 兼容 PMBus 1.2 命令子集 |
| SMBus 规范兼容性 | 支持 | 基于 SMBus 传输协议 |
| I2C 物理层兼容性 | 支持 | 开漏输出，需外部上拉电阻 |
| 总线速率 100 kHz（标准模式） | 支持 | 兼容不支持 Clock Stretching 的主机时，可使用 5~10 kHz |
| 总线速率 400 kHz（快速模式） | 支持 | 最大总线速率 400 kHz |
| PEC（包错误校验，CRC-8） | 支持 | 模块始终检查主机发送的 PEC 并在所有响应中包含 PEC |
| SMBALERT 响应协议 | 支持 | 通过 SMBALERT# 引脚向主机主动报告故障/警告 |
| Clock Stretching | 支持 | 最大时钟低电平周期 35 ms |
| Bus Timeout | 支持 | 符合 SMBus 规定（25 ms ~ 35 ms） |
| 7-bit 设备寻址 | 支持 | 支持通过外部电阻编程配置多个地址 |
| 多地址配置 | 支持 | 通过 ADDR1 引脚外接电阻，支持 14 个可编程地址 + 1 个默认地址 |
| ARA（Alert Response Address, 0x0C） | 支持 | SMBALERT 响应协议的一部分，主机通过读取该地址识别报警设备 |
| SMBus ARP 协议 | 不支持 | 不支持地址解析协议 |
| GROUP 协议（多设备同时寻址） | 不支持 | 不支持多设备广播命令 |
| 10-bit 地址模式 | 不支持 | 仅支持 7-bit 寻址 |
| Host Notify | 不支持 | 不支持从设备主动向主机发送通知 |
| 过程调用（Process Call） | 不支持 | 不支持 R/W Word + 后续操作的事务类型 |

> 协议层详细说明参见第 2 章（PMBus 协议基础），总线时序参见第 4 章（PMBus 传输协议），PEC 机制参见第 6 章（PEC），SMBALERT 机制参见第 7 章。

### H.1.2 PMBus 传输类型支持

| 传输类型 | 支持 | 典型应用命令 |
|----------|------|-------------|
| Send Byte | 支持 | CLEAR_FAULTS、STORE_DEFAULT_ALL、RESTORE_DEFAULT_ALL |
| Read Byte | 支持 | STATUS_VOUT、ON_OFF_CONFIG、CAPABILITY、PMBUS_REVISION |
| R/W Byte | 支持 | OPERATION、WRITE_PROTECT、FAULT_RESPONSE 系列 |
| Read Word | 支持 | READ_VOUT、READ_VIN、READ_IOUT、READ_TEMPERATURE_1、STATUS_WORD |
| R/W Word | 支持 | VOUT_COMMAND、保护阈值、时序命令等 |
| Read Block | 支持 | MFR_ID、MFR_MODEL、MFR_SERIAL 等标识命令 |
| R/W Block | 支持 | MFR_MODULE_DATE_LOC_SN |
| Process Call | 不支持 | — |
| Block Write - Block Read Process Call | 不支持 | — |

> 传输协议详解参见第 4 章。

---

## H.2 命令类别支持矩阵

### H.2.1 系统控制命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| ON/OFF 控制 | OPERATION | 0x01 | 支持（部分功能） | 支持 ON/OFF Immediate 和 Margins (Act on Fault)；不支持 Soft Off with Sequencing 和 Margins (Ignore Faults) |
| ON/OFF 配置 | ON_OFF_CONFIG | 0x02 | 支持 | 读操作；引脚极性由模块代码决定，运行时只读 |
| 故障清除 | CLEAR_FAULTS | 0x03 | 支持 | 清除所有锁存故障状态，释放 SMBALERT# |
| 写保护 | WRITE_PROTECT | 0x10 | 支持 | 标准写保护命令；实际写保护通过 MFR_DEVICE_TYPE 控制 |
| 默认参数保存 | STORE_DEFAULT_ALL | 0x11 | 支持 | 保存到 EEPROM，执行时间 ≤ 500 ms |
| 默认参数恢复 | RESTORE_DEFAULT_ALL | 0x12 | 支持 | 从 EEPROM 恢复至 Operating Memory |
| 设备能力 | CAPABILITY | 0x19 | 支持 | 8-bit 位域，默认值 0xB0 |

> ON/OFF 控制逻辑详见第 9 章，非易失性存储详见第 10 章。

### H.2.2 设备信息与标识命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 协议版本 | PMBUS_REVISION | 0x98 | 支持 | 默认值 0x22 (Part I = 1.2, Part II = 1.2) |
| 制造商 ID | MFR_ID | 0x99 | 支持 | Block Read，默认值 "OMPW" |
| 产品型号 | MFR_MODEL | 0x9A | 支持 | Block Read |
| 硬件版本 | MFR_REVISION | 0x9B | 支持 | Block Read |
| 制造产地 | MFR_LOCATION | 0x9C | 支持 | Block Read |
| 制造日期 | MFR_DATE | 0x9D | 支持 | Block Read |
| 产品序列号 | MFR_SERIAL | 0x9E | 支持 | Block Read |
| 固件版本 | MFR_FW_REV | 0xDB | 支持 | Read Word，格式 0xMj.Mn.Bh.Bl |

### H.2.3 输出电压配置命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 电压数据格式 | VOUT_MODE | 0x20 | 支持（只读） | 定义 VOUT 相关命令的固定指数，默认 0x14（exp = -12） |
| 输出电压设定 | VOUT_COMMAND | 0x21 | 支持 | R/W Word，VOUT Linear 格式 |
| 电压微调偏移 | VOUT_CAL_OFFSET | 0x23 | 支持 | R/W Word，受 MFR_DEVICE_TYPE 写保护锁定 |
| 高裕量电压 | VOUT_MARGIN_HIGH | 0x25 | 支持 | R/W Word，VOUT Linear 格式 |
| 低裕量电压 | VOUT_MARGIN_LOW | 0x26 | 支持 | R/W Word，VOUT Linear 格式 |
| 电压下垂补偿 | VOUT_DROOP | 0x28 | 支持 | R/W Word，单位 mV/A，默认值因产品型号而异 |
| 电压微调 | VOUT_TRIM | 0x22 | 部分产品支持 | 部分产品不支持，参见具体产品 Datasheet |
| 电压上限 | VOUT_MAX | 0x24 | 部分产品支持 | 部分产品不支持，参见具体产品 Datasheet |
| 电压下限 | VOUT_MIN | 0x23（自定义） | 部分产品支持 | 部分产品不支持，参见具体产品 Datasheet |

> 输出电压配置详见第 9 章，数据格式编码参见第 5 章。

### H.2.4 遥测读取命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 输出电压读取 | READ_VOUT | 0x8B | 支持 | VOUT Linear 格式，分辨率 0.244 mV |
| 输入电压读取 | READ_VIN | 0x88 | 支持 | Linear 格式，分辨率 125 mV |
| 输出电流读取 | READ_IOUT | 0x8C | 支持 | Linear 格式，分辨率 146 mA，20A 以下消隐 |
| 温度读取 | READ_TEMPERATURE_1 | 0x8D | 支持 | Linear 格式，分辨率 0.25°C |
| 输出功率读取 | READ_POUT | 0x96 | 部分产品支持 | 部分产品支持，参见具体产品 Datasheet |
| 输入功率读取 | READ_PIN | 0x97 | 部分产品支持 | 部分产品支持，参见具体产品 Datasheet |
| 峰值电流读取 | IOUT_PEAK | 0x91 | 不支持 | — |
| 峰值电压读取 | VOUT_PEAK | 0x95 | 不支持 | — |

> 遥测系统特性详见第 1 章 1.4 节。

### H.2.5 保护阈值命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 输出过压故障限制 | VOUT_OV_FAULT_LIMIT | 0x40 | 支持 | VOUT Linear 格式，自动覆盖特性（最大 = 设定点 + 2V） |
| 输出过压故障响应 | VOUT_OV_FAULT_RESPONSE | 0x41 | 支持（部分） | Response 仅支持 10b；Retry 仅支持 000/111；Delay 仅支持 000 |
| 输出过流故障限制 | IOUT_OC_FAULT_LIMIT | 0x46 | 支持 | Linear 格式 |
| 输出过流故障响应 | IOUT_OC_FAULT_RESPONSE | 0x47 | 支持（部分） | Response 仅支持 11b；Retry 仅支持 000/111；Delay 仅支持 000 |
| 输出过流警告限制 | IOUT_OC_WARN_LIMIT | 0x4A | 支持 | Linear 格式，必须低于故障限制 |
| 过温故障限制 | OT_FAULT_LIMIT | 0x4F | 支持 | Linear 格式 |
| 过温故障响应 | OT_FAULT_RESPONSE | 0x50 | 支持（部分） | Response 仅支持 10b；Retry 仅支持 000/111；Delay 仅支持 000 |
| 过温警告限制 | OT_WARN_LIMIT | 0x51 | 支持 | Linear 格式，必须低于故障限制 |
| 输入过压故障限制 | VIN_OV_FAULT_LIMIT | 0x55 | 支持 | Linear 格式 |
| 输入欠压故障限制 | VIN_UV_FAULT_LIMIT | 0x59 | 部分产品支持 | 部分产品支持，参见具体产品 Datasheet |

> 保护阈值详细说明和交叉检查规则参见第 8 章。FAULT_RESPONSE 位域映射参见附录 E。

### H.2.6 时序配置命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 启动延迟 | TON_DELAY | 0x60 | 支持 | Linear 格式，范围 0 ~ 500 ms，分辨率 0.5 ms |
| 上升时间 | TON_RISE | 0x61 | 支持 | Linear 格式，范围 12 ~ 500 ms，分辨率 0.5 ms |
| 关断延迟 | TOFF_DELAY | 0x64 | 部分产品支持 | 部分产品不支持 Soft Off 时序，参见具体产品 Datasheet |
| 下降时间 | TOFF_FALL | 0x65 | 部分产品支持 | 部分产品不支持 Soft Off 时序，参见具体产品 Datasheet |
| 启动超时 | TON_MAX_FAULT_LIMIT | 0x42 | 不支持 | — |
| 关断超时 | TOFF_MAX_WARN_LIMIT | 0x43 | 不支持 | — |

> 时序配置详见第 9 章。

### H.2.7 PGOOD 配置命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| PGOOD 断言阈值 | POWER_GOOD_ON | 0x5E | 支持 | VOUT Linear 格式 |
| PGOOD 取消断言阈值 | POWER_GOOD_OFF | 0x5F | 支持 | VOUT Linear 格式，与 POWER_GOOD_ON 至少 0.5V 迟滞 |
| PGOOD 极性配置 | MFR_PGOOD_POLARITY | 0xE2 | 支持 | Bit 0 控制极性，默认正逻辑 |

> PGOOD 配置详见第 9 章。

### H.2.8 状态监控命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 总体状态概览 | STATUS_BYTE | 0x78 | 支持 | 8-bit，Bit 7~Bit 1 |
| 扩展状态概览 | STATUS_WORD | 0x79 | 支持 | 16-bit，高字节 = STATUS_BYTE，低字节含多类信息 |
| 输出电压状态 | STATUS_VOUT | 0x7A | 支持（部分位） | Bit 7 (OV Fault)、Bit 4 (UV Fault) 已实现 |
| 输出电流状态 | STATUS_IOUT | 0x7B | 支持（部分位） | Bit 7 (OC Fault)、Bit 5 (OC Warning) 已实现 |
| 输入电压状态 | STATUS_INPUT | 0x7C | 支持（部分位） | Bit 7 (OV Fault)、Bit 4 (UV Fault)、Bit 3 (Module Off) 已实现 |
| 温度状态 | STATUS_TEMPERATURE | 0x7D | 支持（部分位） | Bit 7 (OT Fault)、Bit 6 (OT Warning) 已实现 |
| 通信状态 | STATUS_CML | 0x7E | 支持（部分位） | Bit 7 (INVALID_CMD)、Bit 6 (INVALID_DATA)、Bit 5 (PEC_FAILED) 已实现 |
| 风扇状态 | STATUS_FANS | 0x81 | 不支持 | Omnion Power 模块不含风扇 |
| 存储器状态 | STATUS_MFR_SPECIFIC | 0x80 | 不支持 | — |
| 其他状态 | STATUS_OTHER | 0x7F | 不支持 | — |

> 状态寄存器完整位域映射参见附录 D，故障管理机制详见第 8 章。

### H.2.9 非易失性存储命令

| 命令类别 | 命令 | 命令码 | 支持 | 备注 |
|----------|------|--------|------|------|
| 保存默认参数 | STORE_DEFAULT_ALL | 0x11 | 支持 | 将 Operating Memory 保存到 EEPROM，执行时间 ≤ 500 ms |
| 恢复默认参数 | RESTORE_DEFAULT_ALL | 0x12 | 支持 | 从 EEPROM 恢复到 Operating Memory |
| 保存用户参数 | STORE_USER_ALL | 0x17 | 部分产品支持 | 部分产品不支持独立 User Store，参见具体产品 Datasheet |
| 恢复用户参数 | RESTORE_USER_ALL | 0x18 | 部分产品支持 | 部分产品不支持独立 User Store，参见具体产品 Datasheet |

> 可存储到 NVM 的参数完整列表参见附录 G（NVM 操作摘要），NVM 机制详见第 10 章。

### H.2.10 制造商特定命令

| 命令 | 命令码 | 支持 | 备注 |
|------|--------|------|------|
| MFR_DEVICE_TYPE | 0xD0 | 支持 | 写保护控制（WPE 位）+ 模块名称配置 |
| MFR_FW_REV | 0xDB | 支持（只读） | 固件版本读取 |
| MFR_PGOOD_POLARITY | 0xE2 | 支持 | PGOOD 信号极性配置 |
| MFR_MODULE_DATE_LOC_SN | 0xF0 | 支持 | 模块日期/位置/序列号读写，受写保护锁定 |

### H.2.11 不支持的命令汇总

以下 PMBus 标准命令在 Omnion Power 模块中不支持：

| 命令 | 命令码 | 说明 |
|------|--------|------|
| PAGE | 0x00 | 单输出产品不需要页面切换；多路输出产品支持情况参见具体产品 Datasheet |
| COEFFICIENTS | 0x30 | 不支持 Direct 格式参数配置 |
| VOUT_MIN | — | 部分产品不支持 |
| VOUT_MAX | 0x24 | 部分产品不支持 |
| VOUT_TRIM | 0x22 | 部分产品不支持 |
| VOUT_OV_WARN_LIMIT | 0x42 | 不支持独立过压警告 |
| VOUT_UV_WARN_LIMIT | 0x43 | 不支持独立欠压警告 |
| VOUT_UV_FAULT_LIMIT | 0x44 | 不支持独立欠压故障限制 |
| IOUT_OC_WARN_LIMIT | 0x4A | 支持 |
| VIN_UV_FAULT_LIMIT | 0x59 | 部分产品不支持 |
| TON_MAX_FAULT_LIMIT | 0x42 | 不支持启动超时 |
| TOFF_MAX_WARN_LIMIT | 0x43 | 不支持关断超时 |
| TOFF_DELAY | 0x64 | 部分产品不支持 Soft Off |
| TOFF_FALL | 0x65 | 部分产品不支持 Soft Off |
| STATUS_FANS | 0x81 | 不支持风扇状态 |
| STATUS_MFR_SPECIFIC | 0x80 | 不支持 |
| STATUS_OTHER | 0x7F | 不支持 |
| USER_DATA | 0x33 | 不支持 |
| MFR_SPECIFIC_XX | — | 除上述列出的 MFR 命令外，其余厂商特定命令不支持 |

---

## H.3 数据格式支持

### H.3.1 PMBus 数值数据格式

| 数据格式 | 支持 | 说明 |
|----------|------|------|
| Linear 格式（可变指数） | 支持 | 用于非 VOUT 类数值命令（电流、温度、时序等）。5-bit 指数 N + 11-bit 尾数 Y，Value = Y × 2^N |
| VOUT Linear 格式（固定指数） | 支持 | 用于所有 VOUT 相关命令。16-bit 无符号尾数，指数由 VOUT_MODE (0x20) 指定（默认 exp = -12），分辨率 0.244 mV |
| ULINEAR16（无符号 Linear 16-bit） | 支持 | VOUT Linear 即为 ULINEAR16 格式的特例，用于电压编码 |
| Direct 格式 | 不支持 | 不使用 m、b、R 参数编码 |
| COEFFICIENTS 命令 | 不支持 | 不支持 Direct 格式参数配置 |

### H.3.2 PMBus 字段数据格式

| 字段格式 | 支持 | 说明 |
|----------|------|------|
| 位域格式（Bit Field） | 支持 | 用于控制和状态命令（OPERATION、ON_OFF_CONFIG、FAULT_RESPONSE、STATUS_* 等），每个位具有独立功能含义 |
| 块格式（Block，8-bit 字符） | 支持 | 用于标识命令（MFR_ID、MFR_MODEL 等），第一字节为数据长度 N，后续为 N 字节数据 |

### H.3.3 常用固定指数值

| 固定指数 | 分辨率 | 适用命令类别 |
|----------|--------|-------------|
| -12（由 VOUT_MODE 指定） | 0.244 mV | VOUT 相关命令（VOUT_COMMAND、READ_VOUT、MARGIN 等） |
| -3 | 125 mV | VIN 相关命令（READ_VIN、VIN_ON、VIN_OFF） |
| -3 | 125 mA / 146 mA | IOUT 相关命令（READ_IOUT、IOUT_OC_FAULT_LIMIT 等） |
| -3 | 0.125°C | 温度相关命令（READ_TEMPERATURE_1、OT_FAULT_LIMIT 等） |

> 数据格式编码/解码方法详见第 5 章。

---

## H.4 不支持的 PMBus 功能列表

### H.4.1 完整不支持功能列表

以下功能在 Omnion Power 数字电源模块中不实现：

| 不支持的功能 | 说明 | 影响范围 |
|-------------|------|----------|
| Direct 数据格式 | 仅使用 Linear 格式进行数值编码 | COEFFICIENTS 命令不可用 |
| SMBus ARP 协议 | 不支持地址解析协议 | 设备地址在上电时固定，运行时不可通过 ARP 更改 |
| GROUP 协议 | 不支持多设备同时寻址 | 每次只能与一个从设备通信 |
| 多裕量模式 (Ignore Faults) | OPERATION 命令仅支持 Act on Fault 模式 | 裕量电压触发保护时不忽略故障 |
| Soft Off with Sequencing | 不支持序列化软关断 | OPERATION Bit 6 (TOFF) 在部分产品中为只读 |
| 10-bit 寻址 | 仅支持 7-bit 地址 | 每条总线最多 14 个设备（含地址配置） |
| Host Notify | 不支持从设备主动通知主机 | 故障通知通过 SMBALERT 机制实现 |
| Process Call | 不支持 R/W Word + 后续操作 | — |
| 风扇控制 | 不支持风扇相关命令 | 模块不包含风扇 |
| AVSBus | 不支持 AVSBus 动态电压调节 | OPERATION Bits[5:4] = 11b 无效 |

> 部分功能在特定产品中可能以厂商特定方式实现，参见具体产品 Datasheet。

---

## H.5 可选功能说明

Omnion Power 数字电源模块的产品线覆盖 DC-DC 模块、IBC、Bus Converter、POL 模块、AC-DC PSU 子模块等多种类型。以下功能在不同产品中的支持情况存在差异。

### H.5.1 功能可用性分类

| 功能 | 通用性 | 说明 |
|------|--------|------|
| PMBus 1.2 协议 | 所有产品 | 所有 Omnion Power 数字电源模块均支持 |
| 100 kHz / 400 kHz 总线速率 | 所有产品 | 全产品线通用 |
| PEC 校验 | 所有产品 | 模块始终检查并发送 PEC |
| SMBALERT 响应协议 | 所有产品 | 全产品线支持 |
| STATUS_WORD 等 7 个状态寄存器 | 所有产品 | 完整的状态监控体系 |
| READ_VOUT / READ_VIN / READ_IOUT / READ_TEMPERATURE_1 | 所有产品 | 四路基础遥测 |
| OPERATION 命令 ON/OFF | 所有产品 | 软件开关控制 |
| ON_OFF_CONFIG | 所有产品 | 硬件引脚行为配置 |
| CLEAR_FAULTS | 所有产品 | 故障清除 |
| STORE_DEFAULT_ALL / RESTORE_DEFAULT_ALL | 所有产品 | NVM 存储/恢复 |
| MFR_ID / MFR_MODEL / MFR_SERIAL 等标识命令 | 所有产品 | 完整设备标识 |
| MFR_DEVICE_TYPE 写保护 | 所有产品 | 写保护机制 |
| 裕量调节 (Margin High/Low) | 所有产品 | 生产测试支持 |
| 保护阈值配置 (OVP/OCP/OTP) | 所有产品 | 可配置故障保护 |

| 功能 | 部分产品支持 | 说明 |
|------|-------------|------|
| 多路输出 (PAGE 命令) | 部分产品 | 多路输出模块可能支持页面选择，单路输出模块不需要 |
| TOFF_DELAY / TOFF_FALL | 部分产品 | Soft Off 时序仅在支持的产品中生效 |
| VOUT_TRIM | 部分产品 | 电压微调偏移功能 |
| VOUT_MAX / VOUT_MIN | 部分产品 | 电压上下限约束 |
| VOUT_DROOP | 部分产品 | 下垂补偿（并联均流），标准版默认为 0，带 -A 后缀典型为 2.2 mV/A |
| READ_POUT / READ_PIN | 部分产品 | 功率遥测 |
| VIN_UV_FAULT_LIMIT | 部分产品 | 输入欠压故障限制 |
| STORE_USER_ALL / RESTORE_USER_ALL | 部分产品 | 独立用户存储区 |
| 黑盒故障记录 | 部分产品 | 自动记录故障事件快照 |

### H.5.2 关键可选功能详解

#### 多路输出（PAGE 命令）

PMBus 规范定义 `PAGE (0x00)` 命令用于选择多路输出设备的目标通道。Omnion Power 产品中：

- **单路输出模块**（如 DC-DC 模块、POL）：不需要 PAGE 命令，所有命令默认操作唯一输出通道
- **多路输出模块**（如部分 PSU 子模块）：可能支持 PAGE 命令，具体实现参见产品 Datasheet

> 系统集成时，应先确认目标模块的输出路数，再决定是否需要 PAGE 命令。

#### TOFF 命令（Soft Off）

关断时序命令在部分产品中不支持。具体行为：

- 支持的产品：OPERATION Bit 6 (TOFF) 可读写，模块可按 TOFF_DELAY 和 TOFF_FALL 设定的时序关断
- 不支持的产品：TOFF 位为只读（固定为 0），模块仅支持立即关断

> 系统设计时，如果需要电源按顺序关断，应确认目标产品是否支持 TOFF 命令。

#### 功率遥测（READ_POUT / READ_PIN）

部分 Omnion Power 产品支持输出功率和输入功率的实时遥测：

- **READ_POUT (0x96)**：输出功率，计算方式为 VOUT × IOUT
- **READ_PIN (0x97)**：输入功率

不支持功率遥测的产品中，主机可通过读取 VOUT 和 IOUT 后自行计算功率。注意计算时应使用模块内部校准后的遥测值，而非外部测量值。

> 功率遥测的支持情况和精度参见具体产品 Datasheet。

#### VOUT_DROOP（下垂补偿）

下垂补偿用于多模块并联时的自动均流。Omnion Power 产品的支持情况：

- **标准版产品**：默认 VOUT_DROOP = 0（无下垂）
- **带 -A 后缀产品**：典型 VOUT_DROOP = 2.2 mV/A

下垂补偿值因产品型号和并联需求而异，配置前应联系 OmniOn Power FAE。

---

## H.6 附录引用说明

| 内容 | 参考章节/附录 |
|------|-------------|
| 协议层详细说明 | 第 2 章、第 4 章 |
| 数据格式编码/解码 | 第 5 章 |
| PEC 机制 | 第 6 章 |
| SMBALERT 中断机制 | 第 7 章 |
| 状态寄存器位域详解 | 第 8 章 + 附录 D |
| FAULT_RESPONSE 位域详解 | 附录 E |
| 控制与配置命令使用 | 第 9 章 |
| 非易失性存储机制 | 第 10 章 |
| 完整命令列表 | 附录 A |
| Linear 格式快速参考 | 附录 B |
| 非易失性存储参数列表 | 附录 G（NVM 摘要） |
| ON/OFF 行为摘要 | 附录 F |
| Python 编程示例 | 第 16 章 |
