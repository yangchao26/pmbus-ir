# 附录 D STATUS 寄存器位域映射参考

> 本附录提供 PMBus 7 个状态寄存器的完整位域映射，作为第 8 章的快速查阅参考。每个位域映射表标注了 Fault/Warning 级别、Omnion Power 模块的实际支持情况，以及与 STATUS_BYTE 概要位的对应关系。故障管理的详细讲解参见第 8 章，数值编码方法参见第 5 章。

---

## D.1 STATUS_BYTE（0x78）

`STATUS_BYTE` 提供 8-bit 的总体状态概览，每位对应一类故障或状态。当某个类别出现异常时，对应位被置位，主机据此决定是否进一步读取对应的第二层寄存器。

**传输类型**: Read Byte

**读取方式**: Send Byte 0x78 或 Read Byte（两种方式均可，返回相同数据）

### 位域映射表

| 位 | 名称 | 级别 | 对应第二层寄存器 | 说明 |
|----|------|------|-----------------|------|
| 7 | BUSY | — | — | 模块正在处理命令或执行内部操作 |
| 6 | OFF | — | — | 模块输出处于关闭状态 |
| 5 | VOUT fault | Fault | STATUS_VOUT (0x7A) | 输出电压存在故障条件 |
| 4 | IOUT fault/warning | Fault/Warning | STATUS_IOUT (0x7B) | 输出电流存在故障或警告条件 |
| 3 | INPUT fault | Fault | STATUS_INPUT (0x7C) | 输入电压存在故障条件 |
| 2 | TEMPERATURE fault/warning | Fault/Warning | STATUS_TEMPERATURE (0x7D) | 温度存在故障或警告条件 |
| 1 | CML fault | Fault | STATUS_CML (0x7E) | 通信、存储器或逻辑存在错误 |
| 0 | OTHER | — | — | 厂商特定故障（Omnion Power 模块不支持此位） |

### Omnion Power 模块支持情况

已实现: Bit 7 ~ Bit 1。Bit 0（OTHER）不支持，始终为 0。

> **注意**: `STATUS_BYTE` 不包含 `STATUS_VOUT` 的详细信息。若需同时获取总览和输出电压状态，应使用 `STATUS_WORD (0x79)`。

---

## D.2 STATUS_WORD（0x79）

`STATUS_WORD` 是一个 16-bit 寄存器，由高字节（STATUS_BYTE 摘要）和低字节（多类别故障摘要）组合而成。一次 Read Word 读取即可获取系统级状态概览。

```
STATUS_WORD = [高字节（Bit 15:8）] + [低字节（Bit 7:0）]
```

传输时低字节先传（Little-Endian），即读取返回的第一个字节为低字节，第二个字节为高字节。

**传输类型**: Read Word

### 位域映射表

| 位 | 名称 | 级别 | 说明 |
|----|------|------|------|
| 15 | VOUT fault | Fault | 输出电压存在故障条件（对应 STATUS_VOUT） |
| 14 | IOUT fault/warning | Fault/Warning | 输出电流或功率存在故障或警告条件（对应 STATUS_IOUT） |
| 13 | INPUT fault | Fault | 输入电压存在故障条件（对应 STATUS_INPUT） |
| 12 | MFR_SPECIFIC | — | 厂商特定故障（Omnion Power 模块不支持此位） |
| 11 | POWER_GOOD# negated | — | 电源正常信号被取反（PGOOD 为无效状态） |
| 10 | FANS | — | 风扇故障（Omnion Power 模块不支持此位） |
| 9 | OTHER | — | 其他故障（Omnion Power 模块不支持此位） |
| 8 | UNKNOWN | — | 未知故障（Omnion Power 模块不支持此位） |
| 7 | — | — | 不支持（Omnion Power 模块不支持此位） |
| 6 | OFF | — | 模块输出处于关闭状态 |
| 5 | VOUT Overvoltage | Fault | 输出过压故障（对应 STATUS_VOUT Bit 7） |
| 4 | IOUT Overcurrent | Fault | 输出过流故障（对应 STATUS_IOUT Bit 7） |
| 3 | VIN Undervoltage | Fault | 输入欠压故障（对应 STATUS_INPUT Bit 3/4） |
| 2 | TEMPERATURE fault/warning | Fault/Warning | 温度故障或警告（对应 STATUS_TEMPERATURE） |
| 1 | CML fault | Fault | 通信/存储器故障（对应 STATUS_CML） |
| 0 | — | — | 不支持（Omnion Power 模块不支持此位） |

### Omnion Power 模块支持情况

已实现: Bit 15、14、13、11、6~1。Bit 12（MFR_SPECIFIC）、Bit 10（FANS）、Bit 9（OTHER）、Bit 8（UNKNOWN）、Bit 7、Bit 0 不支持，始终为 0。

> **注意**: `STATUS_WORD` 的低字节并非 `STATUS_VOUT` 寄存器的直接映射。低字节中混合了 OFF、IOUT Overcurrent、VIN Undervoltage 等信息。需要获取各子状态寄存器的完整信息时，应直接读取对应的 `STATUS_xxx` 命令。

---

## D.3 STATUS_VOUT（0x7A）

`STATUS_VOUT` 报告与输出电压相关的所有故障和警告条件。

**传输类型**: Read Byte

### 位域映射表

| 位 | 名称 | 级别 | 对应 STATUS_BYTE 位 | 说明 |
|----|------|------|-------------------|------|
| 7 | VOUT OV Fault | Fault | Bit 5 | 输出过压故障：VOUT 超过 `VOUT_OV_FAULT_LIMIT (0x40)`，模块已执行保护动作（关断） |
| 6 | VOUT OV Warning | Warning | Bit 5 | 输出过压警告（Omnion Power 模块不支持此位） |
| 5 | VOUT UV Warning | Warning | Bit 5 | 输出欠压警告（Omnion Power 模块不支持此位） |
| 4 | VOUT UV Fault | Fault | Bit 5 | 输出欠压故障：VOUT 低于欠压故障阈值 |
| 3 | VOUT MAX Warning | Warning | Bit 5 | VOUT 超过 `VOUT_MAX` 警告阈值（Omnion Power 模块不支持此位） |
| 2 | TON_MAX Fault | Fault | Bit 5 | 启动超时故障（Omnion Power 模块不支持此位） |
| 1 | TOFF_MAX Warning | Warning | Bit 5 | 关断超时警告（Omnion Power 模块不支持此位） |
| 0 | VOUT Tracking Error | Warning | Bit 5 | 电压跟踪误差（Omnion Power 模块不支持此位） |

### Omnion Power 模块支持情况

| 位 | 状态 | 说明 |
|----|------|------|
| 7 | 已实现 | VOUT OV Fault — 对应阈值命令 `VOUT_OV_FAULT_LIMIT (0x40)` |
| 6 | 保留 | 不支持 |
| 5 | 保留 | 不支持 |
| 4 | 已实现 | VOUT UV Fault |
| 3 | 保留 | 不支持 |
| 2 | 保留 | 不支持 |
| 1 | 保留 | 不支持 |
| 0 | 保留 | 不支持 |

> **提示**: VOUT 过压故障触发后，模块将根据 `VOUT_OV_FAULT_RESPONSE (0x41)` 的配置执行关断或重启动作。详见第 8 章。

---

## D.4 STATUS_IOUT（0x7B）

`STATUS_IOUT` 报告与输出电流相关的故障和警告条件。

**传输类型**: Read Byte

### 位域映射表

| 位 | 名称 | 级别 | 对应 STATUS_BYTE 位 | 说明 |
|----|------|------|-------------------|------|
| 7 | IOUT OC Fault | Fault | Bit 4 | 输出过流故障：IOUT 超过 `IOUT_OC_FAULT_LIMIT (0x46)`，模块已执行保护动作 |
| 6 | IOUT OC Warning | Warning | Bit 4 | 输出过流警告（Omnion Power 模块不支持此位） |
| 5 | IOUT OC Warning | Warning | Bit 4 | 输出过流警告：IOUT 超过 `IOUT_OC_WARN_LIMIT (0x4A)` |
| 4 | IOUT POUT Warning | Warning | Bit 4 | 功率过载警告（Omnion Power 模块不支持此位） |
| 3 | 保留 | — | — | 不支持 |
| 2 | 保留 | — | — | 不支持 |
| 1 | 保留 | — | — | 不支持 |
| 0 | 保留 | — | — | 不支持 |

### Omnion Power 模块支持情况

| 位 | 状态 | 说明 |
|----|------|------|
| 7 | 已实现 | IOUT OC Fault — 对应阈值命令 `IOUT_OC_FAULT_LIMIT (0x46)` |
| 6 | 保留 | 不支持 |
| 5 | 已实现 | IOUT OC Warning — 对应阈值命令 `IOUT_OC_WARN_LIMIT (0x4A)` |
| 4 | 保留 | 不支持 |
| 3 | 保留 | 不支持 |
| 2 | 保留 | 不支持 |
| 1 | 保留 | 不支持 |
| 0 | 保留 | 不支持 |

> **提示**: 过流警告（Bit 5）与过流故障（Bit 7）分别对应不同的阈值。警告阈值 `IOUT_OC_WARN_LIMIT` 必须低于故障阈值 `IOUT_OC_FAULT_LIMIT`。数值编码方法参见第 5 章。

---

## D.5 STATUS_INPUT（0x7C）

`STATUS_INPUT` 报告与输入电压相关的故障条件。

**传输类型**: Read Byte

### 位域映射表

| 位 | 名称 | 级别 | 对应 STATUS_BYTE 位 | 说明 |
|----|------|------|-------------------|------|
| 7 | VIN OV Fault | Fault | Bit 3 | 输入过压故障：VIN 超过 `VIN_OV_FAULT_LIMIT (0x55)` |
| 6 | VIN OV Warning | Warning | Bit 3 | 输入过压警告（Omnion Power 模块不支持此位） |
| 5 | VIN UV Warning | Warning | Bit 3 | 输入欠压警告（Omnion Power 模块不支持此位） |
| 4 | VIN UV Fault | Fault | Bit 3 | 输入欠压故障：VIN 低于 `VIN_OFF (0x36)` 阈值 |
| 3 | Unit Off (Low VIN) | — | Bit 3 | 模块因输入电压过低而关闭 |
| 2 | IIN OC Fault | Fault | Bit 3 | 输入过流故障（Omnion Power 模块不支持此位） |
| 1 | IIN OC Warning | Warning | Bit 3 | 输入过流警告（Omnion Power 模块不支持此位） |
| 0 | PIN OP Warning | Warning | Bit 3 | 输入功率过载警告（Omnion Power 模块不支持此位） |

### Omnion Power 模块支持情况

| 位 | 状态 | 说明 |
|----|------|------|
| 7 | 已实现 | VIN OV Fault — 对应阈值命令 `VIN_OV_FAULT_LIMIT (0x55)` |
| 6 | 保留 | 不支持 |
| 5 | 保留 | 不支持 |
| 4 | 已实现 | VIN UV Fault — 与 VIN_OFF (0x36) 阈值相关 |
| 3 | 已实现 | Unit Off (Low VIN) — 模块因输入电压过低自动关闭 |
| 2 | 保留 | 不支持 |
| 1 | 保留 | 不支持 |
| 0 | 保留 | 不支持 |

> **注意**: 输入欠压关闭（Bit 3）与 UVLO（Under-Voltage Lockout）密切相关。当 VIN 低于 `VIN_OFF (0x36)` 阈值时模块自动关闭输出，输入电压恢复到 `VIN_ON (0x35)` 以上后模块才会重新启动。ON/OFF 控制详见第 9 章。

---

## D.6 STATUS_TEMPERATURE（0x7D）

`STATUS_TEMPERATURE` 报告与模块温度相关的故障和警告条件。

**传输类型**: Read Byte

### 位域映射表

| 位 | 名称 | 级别 | 对应 STATUS_BYTE 位 | 说明 |
|----|------|------|-------------------|------|
| 7 | OT Fault | Fault | Bit 2 | 过温故障：温度超过 `OT_FAULT_LIMIT (0x4F)`，模块已执行保护动作 |
| 6 | OT Warning | Warning | Bit 2 | 过温警告：温度超过 `OT_WARN_LIMIT (0x51)`，模块继续运行但已进入警告区域 |
| 5 | UT Warning | Warning | Bit 2 | 欠温警告（Omnion Power 模块不支持此位） |
| 4 | UT Fault | Fault | Bit 2 | 欠温故障（Omnion Power 模块不支持此位） |
| 3 | 保留 | — | — | 不支持 |
| 2 | 保留 | — | — | 不支持 |
| 1 | 保留 | — | — | 不支持 |
| 0 | 保留 | — | — | 不支持 |

### Omnion Power 模块支持情况

| 位 | 状态 | 说明 |
|----|------|------|
| 7 | 已实现 | OT Fault — 对应阈值命令 `OT_FAULT_LIMIT (0x4F)` |
| 6 | 已实现 | OT Warning — 对应阈值命令 `OT_WARN_LIMIT (0x51)` |
| 5 | 保留 | 不支持 |
| 4 | 保留 | 不支持 |
| 3 | 保留 | 不支持 |
| 2 | 保留 | 不支持 |
| 1 | 保留 | 不支持 |
| 0 | 保留 | 不支持 |

> **提示**: 模块温度传感器位于热点 TH1 附近，读数高于环境温度。OT Warning（Bit 6）是系统进行预防性处理（如降低负载、增加散热）的关键信号。温度读数精度为 ±5°C，数值编码参见第 5 章。

---

## D.7 STATUS_CML（0x7E）

`STATUS_CML`（Communication, Memory, Logic）报告总线通信层面的错误，与电源输出运行状态无关。此类错误通常由主机端的命令或数据问题引起。

**传输类型**: Read Byte

### 位域映射表

| 位 | 名称 | 级别 | 对应 STATUS_BYTE 位 | 说明 |
|----|------|------|-------------------|------|
| 7 | INVALID_CMD | Fault | Bit 1 | 无效或不支持的命令：主机发送了模块不认识的命令码 |
| 6 | INVALID_DATA | Fault | Bit 1 | 无效或不支持的数据：命令被识别但数据超出合法范围 |
| 5 | PEC_FAILED | Fault | — | 包错误校验（PEC）失败：PEC 不匹配，事务被拒绝且命令未执行 |
| 4 | MEMORY_FAULT | Fault | Bit 1 | 存储器故障（Omnion Power 模块不支持此位） |
| 3 | PROCESSOR_FAULT | Fault | Bit 1 | 处理器故障（Omnion Power 模块不支持此位） |
| 2 | 保留 | — | — | 不支持 |
| 1 | OTHER_COMM_FAULT | Fault | Bit 1 | 其他通信故障（Omnion Power 模块不支持此位） |
| 0 | OTHER_MEMORY_LOGIC_FAULT | Fault | Bit 1 | 其他存储器或逻辑故障（Omnion Power 模块不支持此位） |

### Omnion Power 模块支持情况

| 位 | 状态 | 说明 |
|----|------|------|
| 7 | 已实现 | INVALID_CMD — 主机发送了不支持的命令码 |
| 6 | 已实现 | INVALID_DATA — 命令被识别但数据值越界 |
| 5 | 已实现 | PEC_FAILED — CRC-8 校验不匹配（PEC 计算方法详见第 6 章） |
| 4 | 保留 | 不支持 |
| 3 | 保留 | 不支持 |
| 2 | 保留 | 不支持 |
| 1 | 保留 | 不支持 |
| 0 | 保留 | 不支持 |

### 主机响应与 STATUS_CML 的关系

| 条件 | 设备总线响应 | STATUS_BYTE Bit 1 | STATUS_CML |
|------|------------|-------------------|------------|
| 支持的命令，有效数据 | ACK + 正常响应 | 不变 | 不变 |
| 不支持的命令 | ACK，设置标志 | 置位 | Bit 7 = 1 |
| 无效数据（越界等） | ACK，设置标志 | 置位 | Bit 6 = 1 |
| PEC 校验失败 | NACK | 不变 | Bit 5 = 1 |
| 写保护状态下的写操作 | 命令被忽略 | 不变 | 不变 |

> **提示**: `STATUS_CML` 中的错误与电源运行状态是独立的。命令被拒绝不意味着电源输出存在异常，仅表示总线通信过程中出现了问题。主机应在关键操作后定期检查 `STATUS_CML` 以发现通信异常。PEC 的计算方法详见第 6 章。

---

## D.8 寄存器总览与跨寄存器关系

### 状态寄存器一览

| 寄存器 | 命令码 | 数据长度 | 传输类型 | 已实现位 | 主要功能 |
|--------|--------|----------|----------|----------|----------|
| STATUS_BYTE | 0x78 | 1 Byte | Read Byte | Bit 7 ~ Bit 1 | 总体概览 |
| STATUS_WORD | 0x79 | 2 Byte | Read Word | Bit 15, 14, 13, 11, 7 ~ 1 | 概览 + VOUT 摘要 |
| STATUS_VOUT | 0x7A | 1 Byte | Read Byte | Bit 7, 4 | 过压/欠压故障 |
| STATUS_IOUT | 0x7B | 1 Byte | Read Byte | Bit 7, 5 | 过流故障/警告 |
| STATUS_INPUT | 0x7C | 1 Byte | Read Byte | Bit 7, 4, 3 | 输入过压/欠压 |
| STATUS_TEMPERATURE | 0x7D | 1 Byte | Read Byte | Bit 7, 6 | 过温故障/警告 |
| STATUS_CML | 0x7E | 1 Byte | Read Byte | Bit 7, 6, 5 | 通信错误 |

### STATUS_WORD 与第二层寄存器的映射关系

| STATUS_WORD 位 | 对应第二层寄存器 | 触发条件 |
|---------------|-----------------|----------|
| Bit 15 | STATUS_VOUT (0x7A) | STATUS_VOUT 中任意 Fault 位被置位 |
| Bit 14 | STATUS_IOUT (0x7B) | STATUS_IOUT 中任意 Fault 或 Warning 位被置位 |
| Bit 13 | STATUS_INPUT (0x7C) | STATUS_INPUT 中任意 Fault 位被置位 |
| Bit 11 | POWER_GOOD# 信号 | PGOOD 信号处于无效状态 |
| Bit 5 | STATUS_VOUT Bit 7 | 输出过压故障 |
| Bit 4 | STATUS_IOUT Bit 7 | 输出过流故障 |
| Bit 3 | STATUS_INPUT Bit 3/4 | 输入欠压故障或模块因低输入关闭 |
| Bit 2 | STATUS_TEMPERATURE (0x7D) | 温度故障或警告 |
| Bit 1 | STATUS_CML (0x7E) | 通信/存储器/逻辑错误 |

> **提示**: 推荐以 `STATUS_WORD (0x79)` 作为健康检查入口。读取一次即可获取系统级状态概览，仅在检测到非零值时才进一步查询对应的第二层 `STATUS_xxx` 寄存器，以减少总线流量。详细的故障监控流程和恢复策略参见第 8 章。

---

**交叉引用**:

- 状态监控与故障管理的详细讲解 → 第 8 章
- 数据格式（8-bit 位域） → 第 5 章
- PEC 校验计算方法 → 第 6 章
- ON/OFF 控制与 VIN_ON/VIN_OFF → 第 9 章
- FAULT_RESPONSE 位域映射 → 附录 E
- 故障管理的 Python 编程示例 → 第 16 章
