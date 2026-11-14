# AN008 内容重复与矛盾检查报告

**检查日期**: 2026-04-30  
**检查范围**: `AN008` 目录下 Markdown 文档  
**处理状态**: 仅记录问题，暂不修正文档正文

---

## 结论摘要

本次检查发现若干跨文件内容冲突，主要集中在 NVM 命令码与存储模型、`ON_OFF_CONFIG` 可写性、`STATUS_WORD` 低字节含义、ARA 地址、`CAPABILITY` 位定义和 Python 示例一致性等方面。

建议先修高优先级问题，因为这些问题会直接影响读者实现 PMBus 主机驱动和调试流程。

---

## 高优先级问题

### 1. NVM 命令码冲突

多数文件使用：

- `STORE_DEFAULT_ALL = 0x11`
- `RESTORE_DEFAULT_ALL = 0x12`

代表位置：

- `AN008_appendix_A_完整命令列表.md:226`
- `AN008_appendix_H_功能支持矩阵.md:172`
- `AN008_ch16_Python编程示例.md:2623`

但以下文件使用了另一组命令码：

- `AN008_ch10_非易失性存储.md:103`：`STORE_DEFAULT_ALL = 0x15`，`RESTORE_DEFAULT_ALL = 0x16`
- `AN008_appendix_G_NVM操作摘要.md:44`：`STORE_DEFAULT_ALL = 0x15`，`RESTORE_DEFAULT_ALL = 0x16`
- 同时将 `STORE_USER_ALL / RESTORE_USER_ALL` 写为 `0x17 / 0x18`

**风险**: 命令码错误会直接导致主机端代码访问错误命令。

**建议**: 以产品实际 Datasheet/命令表为准，统一全书 NVM 命令码。若 Omnion Power 通用实现为 `0x11/0x12`，则第 10 章和附录 G 需要整体修订。

---

### 2. NVM 存储模型互相矛盾

不同文件对 NVM 模型的描述不一致：

- `AN008_appendix_A_完整命令列表.md:222`：称 Omnion Power 产品采用单存储区模型。
- `AN008_ch10_非易失性存储.md:13`：按 `Factory Default + User Store + Operating Memory` 三层模型展开。
- `AN008_appendix_I_FAQ.md:298`：称 `RESTORE_DEFAULT_ALL` 恢复出厂值，且不影响 EEPROM 中用户已保存配置。
- `AN008_ch13_上电与启动行为.md:256`：称 Omnion Power 的 `RESTORE_DEFAULT_ALL` 恢复用户保存配置，而非原始出厂值。

**风险**: 用户无法判断 Store/Restore 是否会覆盖出厂值或用户配置。

**建议**: 先确认目标产品实际 NVM 架构，再统一全书。若通用手册覆盖多种架构，应明确区分“PMBus 标准模型”“Omnion Power 典型实现”“产品相关差异”。

---

### 3. `ON_OFF_CONFIG` 是否可写冲突

以下位置将 `ON_OFF_CONFIG (0x02)` 标为只读或 Read Byte：

- `AN008_appendix_A_完整命令列表.md:14`
- `AN008_appendix_H_功能支持矩阵.md:58`
- `AN008_ch09_控制与配置命令.md:570`
- `AN008_ch16_Python编程示例.md:3016`

但 Python 示例中实际写入该命令：

- `AN008_ch16_Python编程示例.md:763`
- `AN008_ch16_Python编程示例.md:2791`

**风险**: 示例代码会误导用户写只读命令，可能触发 NACK、无效数据或静默忽略。

**建议**: 如果 `ON_OFF_CONFIG` 在 Omnion Power 产品中运行时只读，应删除或改写第 16 章中写 `ON_OFF_CONFIG` 的示例，只保留读取和根据现有配置判断控制路径。

---

### 4. `STATUS_WORD` 低字节说明冲突

`AN008_appendix_A_完整命令列表.md:188` 写：

- `STATUS_WORD = STATUS_BYTE + STATUS_VOUT`

但以下位置明确说明 Omnion Power 实现中低字节不是 `STATUS_VOUT` 的直接映射：

- `AN008_ch08_状态监控与故障管理.md:78`
- `AN008_ch08_状态监控与故障管理.md:114`
- `AN008_appendix_D_STATUS寄存器位域.md:73`

**风险**: 读者可能错误解析 `STATUS_WORD` 低字节。

**建议**: 以第 8 章和附录 D 的实现说明为准，修正附录 A 中的 `STATUS_WORD` 描述。

---

### 5. ARA 地址冲突

多数文件写 ARA 地址为 `0x0C`：

- `AN008_ch07_SMBALERT中断机制.md:99`
- `AN008_appendix_H_功能支持矩阵.md:24`
- `AN008_appendix_I_FAQ.md:171`
- `AN008_ch16_Python编程示例.md:1652`

但第 2 章写为 `0x0A`：

- `AN008_ch02_PMBus协议基础.md:431`
- `AN008_ch02_PMBus协议基础.md:612`
- `AN008_ch02_PMBus协议基础.md:625`

**风险**: ARA 地址错误会导致主机无法识别 SMBALERT 报警设备。

**建议**: 统一为 SMBus Alert Response Address `0x0C`。

---

## 中优先级问题

### 6. `CAPABILITY` 位定义与 Python 示例冲突

正文多处写 `CAPABILITY` 的 Bit 7 指示 PEC 支持：

- `AN008_ch06_包错误校验PEC.md:374`
- `AN008_ch06_包错误校验PEC.md:378`
- `AN008_ch11_设备识别与信息命令.md:131`
- `AN008_appendix_I_FAQ.md:130`

但第 16 章示例中：

- `AN008_ch16_Python编程示例.md:330`：bit 7 写为 SMBALERT 支持，bit 5 写为 PEC。
- `AN008_ch16_Python编程示例.md:2708`：代码使用 `cap & 0x20` 判断 PEC。

**风险**: 初始化代码会错误判断 PEC 支持状态。

**建议**: 以正文确认后的 `CAPABILITY` 位定义为准，修正第 16 章代码和注释。

---

### 7. `PMBUS_REVISION` 传输类型误用

多数文件正确写 `PMBUS_REVISION (0x98)` 为 Read Byte：

- `AN008_ch11_设备识别与信息命令.md:426`
- `AN008_ch14_主机端驱动开发指南.md:98`
- `AN008_ch16_Python编程示例.md:3041`

但以下位置误用：

- `AN008_ch04_PMBus传输协议.md:18`：将其作为 Block Write 配置示例。
- `AN008_ch04_PMBus传输协议.md:330`：写成 `PMBUS_REVISION (0x98)` 配置。
- `AN008_ch15_调试与故障排查.md:119`：称使用已知 Read Word 命令，如 `PMBUS_REVISION (0x98)`。

**风险**: 传输类型错误会误导调试和 PEC 验证。

**建议**: 第 4 章 Block Write 示例改为厂商自定义块写命令或通用占位命令；第 15 章 PEC 验证示例改为实际 Read Word 命令，例如 `READ_VOUT (0x8B)`。

---

### 8. PEC 支持语义过于绝对

以下位置写得较绝对：

- `AN008_ch01_引言.md:199`：模块始终检查主机发送的 PEC 并在响应中包含 PEC。
- `AN008_appendix_H_功能支持矩阵.md:18`：模块始终检查主机发送的 PEC 并在所有响应中包含 PEC。

但第 6 章写：

- `AN008_ch06_包错误校验PEC.md:520`：PEC 是可选功能，由主机决定是否启用；设备在收到带 PEC 的事务时校验 PEC。

**风险**: “所有响应中包含 PEC”可能被理解为无 PEC 读事务也会多返回 PEC 字节。

**建议**: 统一为：“设备支持 PEC；当主机使用带 PEC 的事务时，设备校验 PEC 并在带 PEC 读响应中返回 PEC；无 PEC 事务是否接受以具体产品 Datasheet 为准。”

---

### 9. ARA 多设备仲裁能力表述冲突

以下位置描述 ARA 支持多设备仲裁：

- `AN008_ch07_SMBALERT中断机制.md:185`
- `AN008_appendix_I_FAQ.md:173`

但第 16 章提示：

- `AN008_ch16_Python编程示例.md:1782`：Omnion Power 模块支持 SMBALERT 响应协议，但在多设备共享 SMBALERT# 的场景中不具备总线争用仲裁能力，建议优先逐设备轮询 `STATUS_WORD`。

**风险**: 主机端在多设备报警场景中会选择不同策略。

**建议**: 确认实际硬件是否支持 ARA 多设备仲裁。若不支持，应修改第 7 章和 FAQ，把 ARA 仲裁描述为 SMBus 标准行为，同时明确 Omnion Power 产品限制。

---

## 重复内容

### 1. 第 8 章与附录 D 重复

重复主题：

- `STATUS_WORD` 低字节说明
- `STATUS_CML` 定义
- `STATUS_CML` 与电源运行状态独立
- 输入欠压与 UVLO 说明
- 温度状态提示

代表位置：

- `AN008_ch08_状态监控与故障管理.md`
- `AN008_appendix_D_STATUS寄存器位域.md`

**建议**: 第 8 章保留监控流程、故障处理策略和解释；附录 D 保留完整位域映射表和速查说明。

---

### 2. 第 6 章与附录 C 重复

重复主题：

- CRC-8 查找表
- PEC 查表法说明

代表位置：

- `AN008_ch06_包错误校验PEC.md`
- `AN008_appendix_C_CRC8查找表.md`

**建议**: 第 6 章保留算法原理和计算流程；完整 256 字节查找表只保留在附录 C。

---

### 3. 附录 A 与第 16 章命令速查表重复

重复主题：

- PMBus 命令码、传输类型、说明

代表位置：

- `AN008_appendix_A_完整命令列表.md`
- `AN008_ch16_Python编程示例.md:3009`

**建议**: 第 16 章只保留“本章代码用到的命令子集”，完整清单引用附录 A。

---

## 建议修复顺序

1. 统一 NVM 命令码和 NVM 存储模型。
2. 修正 `ON_OFF_CONFIG` 可写性与 Python 示例。
3. 修正 `STATUS_WORD` 低字节说明。
4. 统一 ARA 地址。
5. 修正 `CAPABILITY` 位定义与 Python 示例。
6. 修正 `PMBUS_REVISION` 传输类型误用。
7. 收敛 PEC 支持语义。
8. 确认 ARA 多设备仲裁能力并统一表述。
9. 合并或弱化重复内容，改为交叉引用。
