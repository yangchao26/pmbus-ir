# 附录 F ON/OFF 行为摘要

> 本附录提供 PMBus ON/OFF 控制的快速参考，以表格形式汇总 OPERATION 命令值、ON_OFF_CONFIG 位域、控制源优先级、CTRL 引脚逻辑、Margin 操作以及常见应用场景。详细讲解参见第 9 章。

---

## F.1 OPERATION 命令值速查表

`OPERATION (0x01)` 是 1 字节位域命令，同时控制输出开关、关断行为和电压来源。

### F.1.1 位域结构

| 位 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----|---|---|---|---|---|---|---|---|
| 名称 | ON/OFF | TOFF | VOUT CMD SOURCE[1] | VOUT CMD SOURCE[0] | MARGIN FAULT RESPONSE[1] | MARGIN FAULT RESPONSE[0] | TRANSITION | Reserved |
| 访问 | r/w | r/w | r/w | r/w | r/w | r/w | r/w | r |

### F.1.2 各位功能

| 位域 | 值 | 含义 |
|------|-----|------|
| **Bit 7 — ON/OFF** | 1 | 模块输出开启 |
| | 0 | 模块输出关闭 |
| **Bit 6 — TOFF** | 0 | 立即关闭（Bit 7=0 时生效） |
| | 1 | 按 TOFF_DELAY + TOFF_FALL 时序关断（Soft Off，需产品支持） |
| **Bits[5:4] — VOUT CMD SOURCE** | 00 | VOUT_COMMAND（正常设定点） |
| | 01 | VOUT_MARGIN_LOW |
| | 10 | VOUT_MARGIN_HIGH |
| | 11 | AVSBus（Omnion Power 产品不支持） |
| **Bits[3:2] — MARGIN FAULT RESPONSE** | 00 | 无效 |
| | 01 | 忽略裕量引起的故障（Ignore Faults） |
| | 10 | 响应裕量引起的故障（Act on Faults，Omnion Power 默认） |
| | 11 | 无效 |
| **Bit 1 — TRANSITION** | — | AVSBus 切换过渡控制（Omnion Power 产品不支持，通常只读） |

### F.1.3 常用 OPERATION 操作值

| 操作 | 数据字节 | 二进制 | 说明 |
|------|---------|--------|------|
| 开启输出 | 0x80 | 1000_0000 | Bit 7=1, 其余默认 |
| 关闭输出（立即） | 0x00 | 0000_0000 | Bit 7=0, Bit 6=0 |
| 关闭输出（按时序） | 0x40 | 0100_0000 | Bit 7=0, Bit 6=1 |
| 裕量高 | 0xA0 | 1010_0000 | Bit 7=1, Bits[5:4]=10 |
| 裕量低 | 0x90 | 1001_0000 | Bit 7=1, Bits[5:4]=01 |
| 正常运行 | 0x80 | 1000_0000 | Bit 7=1, Bits[5:4]=00 |

> **提示**: 修改 OPERATION 位域时，建议先读取当前值，仅修改目标位再写回，避免意外改变其他位状态。

---

## F.2 ON_OFF_CONFIG 位域映射

`ON_OFF_CONFIG (0x02)` 定义模块如何响应 OPERATION 命令和硬件 CTRL 引脚，通常在上电初始化时设置一次。

| 位 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----|---|---|---|---|---|---|---|---|
| 名称 | Reserved | Reserved | Reserved | DEFAULT | OPERATION | CONTROL | POLARITY | ACTION |
| 默认值 | 0 | 0 | 0 | 0 | 0 | 1 | [模块代码决定] | 1 |

### 各位功能

| 位 | 名称 | 值 | 含义 |
|----|------|-----|------|
| 7~5 | Reserved | 0 | 保留位，写 0 |
| 4 | DEFAULT | 0 | 输入电源有效时自动启动（Omnion Power 默认） |
| | | 1 | 不自动启动，需等待 CTRL 引脚和 OPERATION 使能 |
| 3 | OPERATION | 0 | 忽略 OPERATION 命令的 ON/OFF（Omnion Power 默认） |
| | | 1 | 响应 OPERATION 命令的 ON/OFF |
| 2 | CONTROL | 0 | 忽略 CTRL 引脚 |
| | | 1 | 响应 CTRL 引脚使能/禁用（Omnion Power 默认） |
| 1 | POLARITY | 0 | 负逻辑（Active Low）：CTRL 拉低使能 |
| | | 1 | 正逻辑（Active High）：CTRL 拉高使能 |
| 0 | ACTION | 0 | CTRL 关断时按 TOFF_DELAY + TOFF_FALL 时序关断 |
| | | 1 | CTRL 关断时立即关断（Omnion Power 默认） |

> **注意**: POLARITY 位通常由模块代码决定，出厂固定，运行时只读。Omnion Power 产品 ON_OFF_CONFIG 默认值为 0x1D（负逻辑、控制引脚有效、立即关断）。

---

## F.3 控制源优先级表

模块的输出使能由 OPERATION 命令和 CTRL 引脚共同决定，使能条件为逻辑与（AND）。

| ON_OFF_CONFIG 配置 | OPERATION | CTRL 引脚 | 模块输出 |
|--------------------|-----------|-----------|---------|
| 默认（Bit 3=0, Bit 2=1） | 任意 | 使能 | **ON** |
| 默认（Bit 3=0, Bit 2=1） | 任意 | 禁用 | **OFF** |
| Bit 3=1, Bit 2=1 | ON | 使能 | **ON** |
| Bit 3=1, Bit 2=1 | ON | 禁用 | **OFF** |
| Bit 3=1, Bit 2=1 | OFF | 使能 | **OFF** |
| Bit 3=1, Bit 2=1 | OFF | 禁用 | **OFF** |

### 关键规则

1. **默认配置下硬件独占**: Bit 3=0 时，模块完全不响应 OPERATION 命令的 ON/OFF，CTRL 引脚是唯一使能来源
2. **双源使能为 AND 逻辑**: Bit 3=1 且 Bit 2=1 时，OPERATION 和 CTRL 必须同时为使能状态，模块才输出；任一禁用则输出关闭
3. **极性不影响 AND 逻辑**: 正逻辑和负逻辑模块的引脚使能电平相反，但 AND 交互逻辑一致

---

## F.4 CTRL 引脚逻辑速查

| ON_OFF_CONFIG 设置 | CTRL 极性 | CTRL = LOW | CTRL = HIGH |
|--------------------|----------|------------|-------------|
| Bit 1 = 0（POLARITY = 0） | 负逻辑（Active Low） | **使能** | 禁用 |
| Bit 1 = 1（POLARITY = 1） | 正逻辑（Active High） | 禁用 | **使能** |

### 引脚硬件特性

| 特性 | 说明 |
|------|------|
| 使能电平 | 由 POLARITY 位（模块代码）决定 |
| 悬空状态 | 负逻辑模块悬空 = 禁用；正逻辑模块悬空 = 使能 |
| 最小脉宽 | 参见具体产品 Datasheet，不建议频繁切换 |
| 默认极性 | Omnion Power 产品默认为负逻辑（POLARITY = 0） |

> **设计提示**: 负逻辑模块悬空时默认为禁用状态，这是更安全的默认行为——模块上电后不会自动输出，需外部主动拉低 CTRL 引脚才能使能。

---

## F.5 Margin 操作速查

裕量调节（Margining）通过修改 OPERATION 命令的 Bits[5:4]（VOUT CMD SOURCE）切换输出电压来源。

### 裕量操作表

| 操作 | OPERATION Bits[5:4] | 输出电压来源 | 典型数据字节 |
|------|--------------------|---------------|------------|
| 正常运行 | 00 | VOUT_COMMAND（正常设定点） | 0x80 |
| Margin Low | 01 | VOUT_MARGIN_LOW | 0x90 |
| Margin High | 10 | VOUT_MARGIN_HIGH | 0xA0 |
| 取消 Margin | 00 | VOUT_COMMAND（回到正常设定点） | 0x80 |

### 裕量操作流程

1. 将目标裕量电压写入 `VOUT_MARGIN_HIGH (0x25)` 和/或 `VOUT_MARGIN_LOW (0x26)`
2. 修改 `OPERATION` 命令的 Bits[5:4] 切换电压来源
3. 测试完成后将 Bits[5:4] 恢复为 `00`，回到 VOUT_COMMAND

### 安全约束

| 约束 | 说明 |
|------|------|
| VOUT_MARGIN_HIGH > VOUT_MARGIN_LOW | 高裕量值必须大于低裕量值 |
| 故障响应 | Omnion Power 默认为 Act on Faults，裕量电压触发保护时正常响应 |
| 典型裕量范围 | ±5% ~ ±10%（取决于应用需求） |

> **安全提示**: 进入裕量模式后，如果裕量电压触发了过压或欠压保护阈值，故障保护机制将正常响应，模块执行对应的故障响应动作。

---

## F.6 常见 ON/OFF 场景决策表

| 场景 | 推荐操作 | ON_OFF_CONFIG | 说明 |
|------|---------|--------------|------|
| **仅硬件控制**（默认模式） | CTRL 引脚使能/禁用 | 默认值（0x1D） | 最简单方案，适合不需要软件控制的场景 |
| **通过 PMBus 软件控制 ON/OFF** | 写 OPERATION = 0x80/0x00 | Bit 3 置 1 | 须确保 CTRL 引脚已使能，否则 AND 逻辑阻止输出 |
| **硬件 + 软件联合控制** | 同时管理 CTRL 和 OPERATION | Bit 3=1, Bit 2=1 | 双重使能，任一禁用即关断，适合高安全性系统 |
| **生产线裕量测试** | OPERATION = 0xA0/0x90 | 默认值即可 | 先配置 VOUT_MARGIN_HIGH/LOW，再切换 OPERATION |
| **多模块顺序上电** | 配置不同 TON_DELAY 值 | 默认值即可 | 通过 TON_DELAY (0x60) 实现 0~500ms 的上电延迟 |
| **紧急关断** | CTRL 引脚拉至禁用电平，或 OPERATION = 0x00 | ACTION=1（默认） | ACTION=1 时关断立即生效，无需等待时序 |
| **时序关断（Soft Off）** | OPERATION = 0x40（TOFF=1） | 需产品支持 TOFF_DELAY/TOFF_FALL | 关断时按编程时序执行，适用于需要受控放电的场景 |
| **上电自动启动** | 无需额外操作 | DEFAULT=0（出厂默认） | VIN 有效且 CTRL 使能后自动启动 |
| **上电等待外部指令** | 配置后等待 CTRL 或 OPERATION | DEFAULT=1 | 适用于需要严格时序控制的系统 |

---

## 交叉引用

- ON/OFF 控制详细讲解 → 第 9 章
- 上电行为与默认值 → 第 13 章
- 故障响应配置 → 第 8 章
- 时序配置（TON_DELAY / TON_RISE） → 第 9.3 节
- PGOOD 信号配置 → 第 9.4 节
- Python 编程示例 → 第 16 章
- 数据格式（VOUT Linear） → 第 5 章
