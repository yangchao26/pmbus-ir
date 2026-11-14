# 第4章 PMBus 传输协议

> 本章详细讲解 PMBus 在 SMBus/I²C 总线上的各种事务类型，包括字节级时序、读写操作差异、Block 传输机制以及主机端编程注意事项。掌握这些内容是将 PMBus 命令映射到实际总线通信的基础。

---

## 4.1 事务类型总览表

PMBus 复用 SMBus 的事务协议（Transaction Protocol）来实现命令访问。不同命令需要不同的事务类型，取决于数据方向和数据长度。

### 4.1.1 PMBus 标准事务类型

| 事务类型 | 命令码方向 | 数据长度 | 典型用途 | 支持情况 |
|---------|-----------|---------|---------|---------|
| Send Byte | Host → Device | 0 byte | 无参数命令，如 `CLEAR_FAULTS (0x03)` | 必选 |
| Write Byte | Host → Device | 1 byte | 单字节配置，如 `OPERATION (0x01)` | 必选 |
| Write Word | Host → Device | 2 bytes | 双字节参数，如 `VOUT_COMMAND (0x21)` | 必选 |
| Block Write | Host → Device | N bytes | 块写入，如 `PMBUS_REVISION (0x98)` 配置 | 可选 |
| Read Byte | Device → Host | 1 byte | 单字节状态读取 | 必选 |
| Read Word | Device → Host | 2 bytes | 遥测数据读取，如 `READ_VOUT (0x8B)` | 必选 |
| Block Read | Device → Host | N bytes | 块读取，如 `MFR_MODEL (0x9A)` | 可选 |
| Receive Byte | Device → Host | 1 byte | 快速读取，无需指定命令码 | 可选 |
| Process Call | Host ↔ Device | 2 bytes 写 + 2 bytes 读 | 先写后读的原子操作 | 可选 |
| Block Write-Block Read Process Call | Host ↔ Device | N bytes 写 + N bytes 读 | 块级原子操作 | 可选 |

> **提示**: Omnion Power 数字电源产品支持所有必选事务类型，Block 类型命令的支持情况请参见具体产品 Datasheet。

### 4.1.2 事务类型与命令的映射关系

每个 PMBus 命令在实现时必须明确指定使用的事务类型。命令的访问类型（R/W/RW）与事务类型的对应关系如下：

| 访问类型 | 可用事务类型 | 说明 |
|---------|-------------|------|
| W (Write Only) | Send Byte / Write Byte / Write Word / Block Write | 根据数据长度选择 |
| R (Read Only) | Read Byte / Read Word / Block Read / Receive Byte | 根据数据长度选择 |
| R/W (Read/Write) | 写操作：Write Byte/Word/Block<br>读操作：Read Byte/Word/Block | 同一命令支持双向访问 |

> **重要**: 命令的 R/W 标记仅表示访问方向，实际实现时必须映射到具体的 SMBus 事务类型。例如 `READ_VOUT` 标记为 R，实际使用 Read Word 事务。

---

## 4.2 写操作事务详解

写操作用于主机向设备发送命令或写入配置参数。所有写操作事务都以 START 条件开始，以 STOP 条件结束，方向始终为 Host → Device。

> 关于 START、STOP、ACK、NACK 的详细定义，详见第 2 章。

### 4.2.1 Send Byte 事务

Send Byte 是最简单的写操作，仅发送命令码，不携带数据字节。适用于无需参数的控制命令。

**典型应用**:
- `CLEAR_FAULTS (0x03)` — 清除故障状态
- `STORE_USER_ALL (0x15)` — 保存用户配置到 NVM
- `RESTORE_USER_ALL (0x16)` — 从 NVM 恢复用户配置

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  P
│       │              │        │         │      │
│       │              │        │         │      └── STOP 条件
│       │              │        │         └───────── 设备 ACK
│       │              │        └─────────────────── 命令码 (8-bit)
│       │              └──────────────────────────── 设备 ACK
│       └─────────────────────────────────────────── 7-bit 地址 + W(0)
└─────────────────────────────────────────────────── START 条件
```

**时序说明**:

| 阶段 | 字节内容 | 发送方 | 响应 |
|-----|---------|-------|------|
| START | - | Host | 总线占用 |
| 设备地址 | `0bAAAAAAA0` | Host | 设备 ACK |
| 命令码 | Command Code | Host | 设备 ACK |
| STOP | - | Host | 总线释放 |

[TODO: 图表 — Send Byte 事务时序图]
> 参考图片: pic/AN304_p17_img1_403x307.jpeg (上半部分)
> 图中应包含: START、SlaveAddr+W、Command、ACK、STOP 的完整时序

### 4.2.2 Write Byte 事务

Write Byte 在命令码后携带 1 字节数据，用于设置单字节参数。

**典型应用**:
- `OPERATION (0x01)` — 设置操作模式（Bit 7 控制输出使能）
- `ON_OFF_CONFIG (0x02)` — 配置开关机方式
- `VOUT_MODE (0x20)` — 设置输出电压格式

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  Data  -  ACK  -  P
```

**数据字节格式**:

Write Byte 的数据为单个 8-bit 字节，格式取决于具体命令：

| 命令 | 数据格式 | 说明 |
|-----|---------|------|
| `OPERATION` | Bitfield | Bit 7: Enable, Bit 6-5: Margin |
| `VOUT_MODE` | Bitfield | Bit 7-5: Mode, Bit 4-0: 参数 |
| `PAGE` | Unsigned 8-bit | 选择多路输出的页码 |

> 关于数值编码格式的详细说明，详见第 5 章。

[TODO: 图表 — Write Byte 事务时序图]
> 图中应包含: START、SlaveAddr+W、Command、Data、ACK、STOP 的完整时序

### 4.2.3 Write Word 事务

Write Word 在命令码后携带 2 字节数据，是 PMBus 最常用的写操作类型。数据采用**低字节在前（Little Endian）**的传输顺序。

**典型应用**:
- `VOUT_COMMAND (0x21)` — 设置输出电压
- `VOUT_MARGIN_HIGH (0x25)` — 设置电压裕量上限
- `TON_DELAY (0x60)` — 设置启动延迟
- `VOUT_OV_FAULT_LIMIT (0x40)` — 设置过压保护阈值

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  DataLow  -  ACK  -  DataHigh  -  ACK  -  P
```

**数据字节顺序**:

| 传输顺序 | 字节内容 | 说明 |
|---------|---------|------|
| 第 1 字节 | Data Low Byte | 低 8-bit |
| 第 2 字节 | Data High Byte | 高 8-bit |

**示例**: 写入 `VOUT_COMMAND = 0x0A00`（Linear16 格式，表示 1.25V）

```
传输字节序列:
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Command 0x21│ DataLow 0x00│ DataHigh 0x0A│    ACK      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

> 注意: 虽然物理值 0x0A00 的高字节是 0x0A，但在总线上先传输低字节 0x00。

[TODO: 图表 — Write Word 事务时序图]
> 参考图片: pic/AN304_p19_img1_483x453.jpeg
> 图中应包含: START、SlaveAddr+W、Command、DataLow、DataHigh、ACK、STOP 的完整时序

### 4.2.4 带 PEC 的写操作

当启用包错误校验（Packet Error Check, PEC）时，写操作在数据字节后附加 1 字节 PEC 校验码。

**Write Word + PEC 时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  DataLow  -  ACK  -  DataHigh  -  ACK  -  PEC  -  ACK  -  P
```

**PEC 计算范围**:

PEC 覆盖从设备地址到所有数据字节的完整传输内容：
- 设备地址（含 R/W 位）
- 命令码
- 所有数据字节

> 关于 PEC 的详细计算方法，详见第 6 章。

[TODO: 图表 — Write Word with PEC 事务时序图]
> 参考图片: pic/AN304_p19_img1_483x453.jpeg (含 PEC 字节)
> 图中应包含: 完整写序列 + PEC 字节位置

---

## 4.3 读操作事务详解

读操作用于主机从设备获取状态、遥测数据或配置信息。读操作的关键特征是使用 **REPEATED START（重复起始条件）** 来改变总线方向。

### 4.3.1 为什么需要 REPEATED START

读操作分为两个阶段：
1. **写阶段**: 主机发送命令码，告诉设备要读取哪个寄存器
2. **读阶段**: 设备返回数据

由于 SMBus/I²C 总线的方向由 R/W 位决定，而 R/W 位只在地址字节中，因此需要：

```
阶段 1 (写方向): START + SlaveAddr+W + Command
阶段 2 (读方向): REPEATED START + SlaveAddr+R + Data + STOP
```

**使用 REPEATED START 的原因**:

| 原因 | 说明 |
|-----|------|
| 方向切换 | 从写方向切换到读方向需要重新发送地址字节 |
| 总线占用 | REPEATED START 不释放总线，防止其他主机插入事务 |
| 原子性 | 确保命令码和数据读取是连续的原子操作 |

> 如果不使用 REPEATED START，而使用 STOP + START，可能导致其他主机抢占总线，造成读取错误的数据。

### 4.3.2 Read Byte 事务

Read Byte 读取 1 字节数据，适用于单字节状态或配置读取。

**典型应用**:
- `STATUS_BYTE (0x78)` — 读取总体状态
- `STATUS_TEMPERATURE (0x7D)` — 读取温度状态
- `PAGE (0x00)` — 读取当前页码

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  Sr  -  SlaveAddr+R  -  ACK  -  Data  -  NACK  -  P
```

**详细时序分解**:

| 阶段 | 字节/信号 | 发送方 | 说明 |
|-----|----------|-------|------|
| START | S | Host | 总线占用，开始事务 |
| 设备地址(写) | `0bAAAAAAA0` | Host | 7-bit 地址 + W(0) |
| ACK | A | Device | 设备响应 |
| 命令码 | Command | Host | 指定要读取的寄存器 |
| ACK | A | Device | 设备确认命令 |
| REPEATED START | Sr | Host | 方向切换，不释放总线 |
| 设备地址(读) | `0bAAAAAAA1` | Host | 7-bit 地址 + R(1) |
| ACK | A | Device | 设备准备发送数据 |
| 数据字节 | Data | Device | 寄存器数据 |
| NACK | N | Host | 主机表示不再读取 |
| STOP | P | Host | 总线释放，事务结束 |

> **注意**: 读操作的最后一个字节由主机发送 NACK，表示读取完成。

[TODO: 图表 — Read Byte 事务时序图]
> 图中应包含: 写阶段 + Sr + 读阶段的完整时序，标注方向切换点

### 4.3.3 Read Word 事务

Read Word 读取 2 字节数据，是遥测命令的标准事务类型。数据同样采用**低字节在前**的传输顺序。

**典型应用**:
- `READ_VOUT (0x8B)` — 读取输出电压
- `READ_IOUT (0x8C)` — 读取输出电流
- `READ_TEMPERATURE_1 (0x8D)` — 读取温度
- `READ_PIN (0x97)` — 读取输入功率
- `STATUS_WORD (0x79)` — 读取 16-bit 状态字

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  Sr  -  SlaveAddr+R  -  ACK  -  DataLow  -  ACK  -  DataHigh  -  NACK  -  P
```

**数据重组**:

主机接收到的两个字节需要按 Little Endian 重组为 16-bit 值：

```python
# 接收到的字节顺序: [LowByte, HighByte]
value_16bit = (HighByte << 8) | LowByte
```

**示例**: 读取 `READ_VOUT` 返回 [0x00, 0x0A]

```
接收字节:
┌─────────────┬─────────────┐
│  Byte 1     │  Byte 2     │
│  0x00       │  0x0A       │
│  (Low)      │  (High)     │
└─────────────┴─────────────┘
            ↓
重组: 0x0A00
```

> 关于 Linear11 / Linear16 数据格式的解码，详见第 5 章。

[TODO: 图表 — Read Word 事务时序图]
> 参考图片: pic/AN304_p18_img1_561x515.jpeg
> 图中应包含: 完整读序列，标注 LowByte、HighByte、NACK 位置

### 4.3.4 带 PEC 的读操作

Read Word + PEC 在数据字节后附加 1 字节 PEC 校验码，由设备计算并发送。

**Read Word + PEC 时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  Sr  -  SlaveAddr+R  -  ACK  -  DataLow  -  ACK  -  DataHigh  -  ACK  -  PEC  -  NACK  -  P
```

**PEC 计算范围**:

读操作的 PEC 覆盖：
- 第一阶段: 设备地址(写) + 命令码
- 第二阶段: 设备地址(读) + 数据字节

> 主机在接收到 PEC 字节后发送 NACK，然后 STOP。

[TODO: 图表 — Read Word with PEC 事务时序图]
> 参考图片: pic/AN304_p20_img1_531x391.jpeg
> 图中应包含: 完整读序列 + PEC 字节位置

---

## 4.4 Block Read/Write 事务

Block 事务用于传输可变长度的数据块，适用于字符串、数组或批量数据。

### 4.4.1 Block Write 事务

Block Write 在命令码后先发送字节计数（Byte Count），再发送实际数据。

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  ByteCount  -  ACK  -  Data[0]  -  ACK  -  ...  -  Data[N-1]  -  ACK  -  P
```

**字节计数字段**:

| 字段 | 位置 | 说明 |
|-----|------|------|
| Byte Count | Command 后的第 1 字节 | 指示后续数据字节数 N (1-255) |
| Data[0] ~ Data[N-1] | 后续 N 字节 | 实际数据内容 |

**典型应用**:
- `PMBUS_REVISION (0x98)` 配置（部分设备）
- 厂商自定义批量配置命令

> **注意**: Block Write 的字节计数不包括 PEC 字节。如果启用 PEC，PEC 在最后一个数据字节之后。

### 4.4.2 Block Read 事务

Block Read 从设备读取可变长度数据块，设备自动返回字节计数和数据。

**字节级时序**:

```
S  -  SlaveAddr+W  -  ACK  -  Command  -  ACK  -  Sr  -  SlaveAddr+R  -  ACK  -  ByteCount  -  ACK  -  Data[0]  -  ACK  -  ...  -  Data[N-1]  -  NACK  -  P
```

**字节计数的作用**:

| 特性 | 说明 |
|-----|------|
| 动态长度 | 主机无需预先知道数据长度 |
| 安全边界 | 防止缓冲区溢出 |
| 协议自描述 | 数据格式内嵌在传输中 |

**典型应用**:
- `MFR_MODEL (0x9A)` — 读取设备型号字符串
- `MFR_REVISION (0x9B)` — 读取固件版本
- `MFR_SERIAL (0x9E)` — 读取序列号

**主机端处理流程**:

1. 发送命令码（如 `MFR_MODEL`）
2. REPEATED START，切换为读方向
3. 读取 Byte Count（N）
4. 循环读取 N 个数据字节，每个字节发送 ACK
5. 最后一个字节发送 NACK
6. STOP

> **重要**: Block Read 的字节计数最大为 255。实际应用中，PMBus 字符串通常以 ASCII 编码，不一定以 NULL 结尾，主机应根据 Byte Count 确定字符串长度。

[TODO: 图表 — Block Read 事务时序图]
> 参考图片: pic/AN304_p18_img1_561x515.jpeg
> 图中应包含: Byte Count 字段位置，多字节数据传输示意

### 4.4.3 Block 事务的注意事项

| 注意事项 | 说明 |
|---------|------|
| 兼容性 | 并非所有 PMBus 设备都支持 Block 事务，需查阅 Datasheet |
| 最大长度 | SMBus 限制 Block 最大 32 字节，PMBus 可扩展至 255 字节 |
| 超时处理 | 大数据块传输需考虑总线超时 |
| PEC 位置 | PEC 在所有数据字节之后，不包括 Byte Count |

---

## 4.5 Send Byte 与 Receive Byte

### 4.5.1 Send Byte 适用场景

Send Byte 是最简单的命令执行方式，适用于：

| 场景 | 命令示例 | 说明 |
|-----|---------|------|
| 故障清除 | `CLEAR_FAULTS` | 清除所有锁存的故障状态 |
| 配置保存 | `STORE_USER_ALL` | 将 RAM 配置写入 NVM |
| 配置恢复 | `RESTORE_USER_ALL` | 从 NVM 恢复配置 |
| 复位操作 | `MFR_RESET`（厂商自定义）| 软件复位 |

**实现要点**:

- 命令码即操作本身，无需额外参数
- 设备收到命令后立即执行
- 通常无返回值（除非出错 NACK）

### 4.5.2 Receive Byte 适用场景

Receive Byte 是一种特殊的读操作，**不需要指定命令码**，直接读取设备当前默认寄存器的值。

**字节级时序**:

```
S  -  SlaveAddr+R  -  ACK  -  Data  -  NACK  -  P
```

**适用场景**:

| 场景 | 说明 |
|-----|------|
| 快速轮询 | 主机定期读取同一寄存器，无需重复发送命令码 |
| 简化协议 | 减少总线事务时间 |
| 兼容 SMBus | SMBus Alert Response Address (ARA) 协议使用 Receive Byte |

**默认寄存器**:

设备上电后，Receive Byte 的默认目标寄存器通常是：
- `STATUS_BYTE` 或
- 厂商自定义的遥测值

> 注意: PMBus 标准中 Receive Byte 不是主要事务类型，大多数遥测命令需要显式指定命令码。Receive Byte 主要用于 SMBALERT 响应，详见第 7 章。

---

## 4.6 完整事务时序图汇总

### 4.6.1 写操作事务对比

| 事务类型 | 总线字节数 | 时序简图 |
|---------|-----------|---------|
| Send Byte | 2 | `S - A+W - A - CMD - A - P` |
| Write Byte | 3 | `S - A+W - A - CMD - A - D - A - P` |
| Write Word | 4 | `S - A+W - A - CMD - A - DL - A - DH - A - P` |
| Write Word + PEC | 5 | `S - A+W - A - CMD - A - DL - A - DH - A - PEC - A - P` |

### 4.6.2 读操作事务对比

| 事务类型 | 总线字节数 | 时序简图 |
|---------|-----------|---------|
| Read Byte | 4 | `S - A+W - A - CMD - A - Sr - A+R - A - D - N - P` |
| Read Word | 5 | `S - A+W - A - CMD - A - Sr - A+R - A - DL - A - DH - N - P` |
| Read Word + PEC | 6 | `S - A+W - A - CMD - A - Sr - A+R - A - DL - A - DH - A - PEC - N - P` |

### 4.6.3 符号说明

| 符号 | 含义 |
|-----|------|
| S | START 条件 |
| P | STOP 条件 |
| Sr | REPEATED START 条件 |
| A+W | 7-bit 设备地址 + Write 位(0) |
| A+R | 7-bit 设备地址 + Read 位(1) |
| CMD | 命令码 (8-bit) |
| D / DL / DH | 数据字节 / 低字节 / 高字节 |
| A | ACK (SDA 拉低) |
| N | NACK (SDA 保持高) |
| PEC | 包错误校验字节 |

[TODO: 图表 — 完整事务时序对比图]
> 图中应包含: Send Byte、Write Word、Read Word、Block Read 四种典型事务的并列对比

---

## 4.7 主机端编程注意事项

### 4.7.1 地址字节格式

SMBus/I²C 地址字节由 7-bit 设备地址和 1-bit R/W 标志组成：

```
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ A6 │ A5 │ A4 │ A3 │ A2 │ A1 │ A0 │R/W │
└────┴────┴────┴────┴────┴────┴────┴────┘
  └──────── 7-bit Device Address ────────┘
                                         │
                                    0=Write, 1=Read
```

**地址计算示例**:

- 设备地址 0x50 (7-bit) → 写地址字节: `0xA0`，读地址字节: `0xA1`
- 设备地址 0x20 (7-bit) → 写地址字节: `0x40`，读地址字节: `0x41`

> 注意: 某些文档使用 8-bit 地址表示（包含 R/W 位），编程时需确认地址格式。

### 4.7.2 字节序处理

PMBus 使用 **Little Endian**（低字节在前）：

```python
# 发送 Write Word: 值 0x0A00
value = 0x0A00
data_low = value & 0xFF      # 0x00
data_high = (value >> 8) & 0xFF  # 0x0A
# 发送顺序: [data_low, data_high]

# 接收 Read Word: 字节 [0x00, 0x0A]
received = [0x00, 0x0A]
value = (received[1] << 8) | received[0]  # 0x0A00
```

### 4.7.3 ACK/NACK 处理

| 场景 | 主机行为 | 说明 |
|-----|---------|------|
| 发送地址后 | 读取 ACK | ACK=0 表示设备存在 |
| 发送数据后 | 读取 ACK | ACK=0 表示设备已接收 |
| 接收数据时 | 发送 ACK | 继续接收下一字节 |
| 接收最后一个字节 | 发送 NACK | 表示读取完成 |

### 4.7.4 超时与错误处理

| 错误类型 | 检测方法 | 建议处理 |
|---------|---------|---------|
| 设备无响应 | 地址字节 NACK | 重试 3 次，检查地址和供电 |
| 数据 NACK | 数据字节 NACK | 检查命令是否支持，数据是否越界 |
| 时钟拉伸超时 | SCL 长时间低电平 | 复位总线，检查设备状态 |
| PEC 错误 | 校验和不匹配 | 重传，记录通信质量 |
| 总线忙 | START 失败 | 等待或复位总线 |

### 4.7.5 事务间隔

连续事务之间需要满足：

| 参数 | 最小值 | 说明 |
|-----|-------|------|
| 总线空闲时间 | 1.3 µs (100 kHz) | STOP 到下一个 START |
| 设备处理时间 | [参见具体产品 Datasheet] | 写操作后到读操作的间隔 |
| NVM 写入时间 | [参见具体产品 Datasheet] | `STORE_USER_ALL` 后需等待 |

### 4.7.6 编程接口选择

主机端实现 PMBus 通信可选择以下接口：

| 接口类型 | 优点 | 缺点 |
|---------|------|------|
| SMBus 控制器 | 硬件处理协议细节，支持 PEC | 依赖特定硬件 |
| I²C 主控制器 + 软件协议 | 通用性强 | 需软件实现 SMBus 特性 |
| USB-I²C 桥接器 | 开发调试方便 | 速度受限，不适合量产 |

> 关于 Python 编程示例，详见第 16 章。

---

## 本章小结

- PMBus 定义了多种事务类型（Send Byte、Write Byte/Word、Read Byte/Word、Block Read/Write），不同命令需要映射到具体的事务类型
- 读操作必须使用 REPEATED START 切换总线方向，确保命令码和数据读取的原子性
- 多字节数据采用 Little Endian 传输（低字节在前），主机需要正确重组数据
- Block 事务使用字节计数字段指示数据长度，提供动态长度支持
- 主机端编程需注意地址格式、字节序、ACK/NACK 处理以及适当的错误恢复机制

---

## 参考文档

- PMBus Specification Revision 1.3.1, Part I, Section 5: Transport Protocol
- SMBus Specification Version 3.3.1, Section 4: SMBus Protocol
- AN304: PMBus Communication Protocol Guide
