# 附录 G NVM 操作摘要

> 本附录提供非易失性存储（Non-Volatile Memory, NVM）操作的快速参考，涵盖存储器模型关系、Store/Restore 命令速查、操作前置条件、安全策略以及上电恢复行为。NVM 的详细讲解参见第 10 章。

---

## G.1 存储器模型关系

PMBus 设备内部维护三层参数存储区域，其关系如下：

```text
┌─────────────────────────────┐
│   Factory Default (NVM)    │  ← 出厂校准写入，通常不可被用户修改
│   （出厂默认配置）            │
└──────────┬──────────────────┘
           │ RESTORE_DEFAULT_ALL (0x15)
           ↓
┌─────────────────────────────┐
│   User Store (NVM)         │  ← 用户通过 STORE_USER_ALL 保存的配置
│   （用户配置区）              │
└──────────┬──────────────────┘
           │ STORE_USER_ALL (0x15) ↑ / RESTORE_USER_ALL (0x16) ↓
           ↓
┌─────────────────────────────┐
│   Operating Memory (RAM)   │  ← Host 通过 PMBus 写命令直接修改
│   （运行内存，掉电丢失）       │
└─────────────────────────────┘
```

**数据流方向说明**：

- **Store（保存）**：Operating Memory → User Store / Default Store（RAM 向下写入 NVM）
- **Restore（恢复）**：User Store / Default Store → Operating Memory（NVM 向上加载到 RAM）
- **上电恢复方向**：上电时从 NVM 向 RAM 加载（Factory Default 先加载，User Store 后覆盖）

> **提示**：不同产品可能采用双存储区模型、单存储区模型或无用户可写 NVM。三种存储架构变体详见第 10.2 节。使用前应查阅具体产品 Datasheet 确认存储架构。

---

## G.2 Store/Restore 命令速查表

| 命令 | 命令码 | 数据方向 | 传输类型 | 说明 |
|------|--------|----------|----------|------|
| `STORE_DEFAULT_ALL` | `0x15` | 写入 | Send Byte | 将 Operating Memory 保存到 Default Store |
| `RESTORE_DEFAULT_ALL` | `0x16` | 写入 | Send Byte | 将 Default Store 加载到 Operating Memory |
| `STORE_USER_ALL` | `0x17` | 写入 | Send Byte | 将 Operating Memory 保存到 User Store |
| `RESTORE_USER_ALL` | `0x18` | 写入 | Send Byte | 将 User Store 加载到 Operating Memory |

> **注意**：命令码为 PMBus 规范标准值。部分产品实现可能使用不同命令码（如某些产品将 `STORE_DEFAULT_ALL` 映射为 `0x11`、`RESTORE_DEFAULT_ALL` 映射为 `0x12`），具体以产品 Datasheet 为准。

**各命令简要语义**：

| 命令 | 操作 | 典型使用场景 |
|------|------|-------------|
| `STORE_DEFAULT_ALL` | RAM → Default Store | 生产校准阶段写入出厂基线（通常被禁用） |
| `RESTORE_DEFAULT_ALL` | Default Store → RAM | 恢复出厂设置、系统维护、故障排查 |
| `STORE_USER_ALL` | RAM → User Store | 保存用户定制配置，确保掉电后持久化 |
| `RESTORE_USER_ALL` | User Store → RAM | 放弃当前调试修改，回到上次保存的用户配置 |

---

## G.3 Store/Restore 操作前置条件

| 操作 | 前置条件 | 预期时间 | 注意事项 |
|------|----------|----------|----------|
| `STORE_DEFAULT_ALL` | 写保护已解除（如需密码/解锁命令）；输出关闭 | ≤ 500ms（典型值，参见具体产品 Datasheet） | 通常被禁用，写入期间设备可能 NACK 后续请求或报告 busy |
| `RESTORE_DEFAULT_ALL` | 无特殊前置条件 | 即时完成 | 在双存储区模型中恢复出厂基线；在单存储区模型中恢复最近一次 Store 值 |
| `STORE_USER_ALL` | 输出关闭（建议）；所有参数调整已完成并读回验证 | ≤ 500ms（典型值，参见具体产品 Datasheet） | 写入期间不应发送额外命令；掉电可能导致 User Store 数据损坏 |
| `RESTORE_USER_ALL` | 无特殊前置条件 | 即时完成 | 不影响 User Store 本身的数据 |

**通用前置条件汇总**：

1. **输出关闭**：Store 操作期间建议保持输出关闭，避免配置不一致。
2. **写保护解除**：受 `WRITE_PROTECT (0x10)` 或厂商特定写保护机制（如 `MFR_DEVICE_TYPE` 的 WPE 位）保护的参数，需先解除写保护。
3. **写入次数限制**：NVM（EEPROM / Flash）有最大擦写次数限制（典型值：100K ~ 1M 次），不应允许高频写入。避免在调试循环中频繁执行 Store。
4. **参数先验证**：Store 前应读回关键参数确认其值正确，错误的参数一旦写入 NVM 可能影响设备安全运行。
5. **通信中断**：Store 操作期间不应发送额外 PMBus 命令，部分设备会在 Store 完成前 NACK 后续请求或通过 `STATUS_BYTE` / `STATUS_WORD` 报告 busy 状态。

---

## G.4 NVM 操作安全策略

### G.4.1 何时执行 Store

| 场景 | 推荐操作 | 说明 |
|------|----------|------|
| 初始配置完成 | 执行一次 `STORE_USER_ALL` | 所有参数调整完成后集中写入，避免多次 Store |
| 生产校准 | 执行 `STORE_DEFAULT_ALL`（若允许） | 通常需要密码或专用解锁命令 |
| 上电初始化阶段 | 不建议立即 Store | 等待系统稳定后再执行 |
| 日常运行 | 不需要 | 仅在参数变更后执行 |

### G.4.2 写入失败处理

| 失败类型 | 表现 | 处理方式 |
|----------|------|----------|
| Store 期间掉电 | User Store 数据可能损坏（checksum 失败） | 上电时设备检测到无效 User Store，自动回退到 Factory Default |
| Store 命令被 NACK | 设备 busy 或不支持 | 等待后重试；若持续 NACK 则检查设备 Store 支持情况 |
| 写入参数被拒绝 | `STATUS_CML` 的 `INVALID_DATA` 标志置位 | 检查参数是否越界或交叉检查未通过，修正后重新写入 |
| 写保护未解除 | 命令被静默忽略 | 先通过 `WRITE_PROTECT` 或厂商特定命令解除写保护 |

### G.4.3 恢复出厂值流程

当需要将设备恢复到出厂默认配置时：

```text
1. 发送 RESTORE_DEFAULT_ALL (0x16)
   → Factory Default 加载到 Operating Memory

2. （可选）执行 STORE_DEFAULT_ALL (0x15) 或 STORE_USER_ALL (0x17)
   → 覆盖 User Store / Default Store，确保下次上电不从旧配置启动
   注意：部分设备的 RESTORE_DEFAULT_ALL 已自动覆盖 User Store

3. 断电重启
   → 设备从出厂默认值启动
```

> **提示**：系统设计时应预留恢复手段，确保可以通过 `RESTORE_DEFAULT_ALL` 回到安全状态。编程示例详见第 16 章。

---

## G.5 上电自动恢复行为

设备上电时，参数加载遵循以下固定顺序：

```text
Power On
  │
  ├─ Step 1: 加载 Factory Default → Operating Memory
  │
  ├─ Step 2: 检查 User Store 是否有效（valid flag / checksum）
  │
  ├─ Step 3: 若 User Store 有效 → 用 User Store 覆盖 Operating Memory
  │          若 User Store 无效 → 保持 Factory Default
  │
  └─ Step 4: Operating Memory 即为当前运行参数
```

**恢复后的默认状态**：

| 行为 | 说明 |
|------|------|
| User Store 优先 | 如果 User Store 中有有效数据，上电后会覆盖 Factory Default 的对应参数 |
| 无效 User Store 回退 | 如果 User Store 的校验和不通过或 valid flag 未置位，设备将从 Factory Default 启动 |
| RAM 临时修改不保存 | Host 在运行期间通过 PMBus 写命令修改的参数仅驻留在 Operating Memory 中，掉电即丢失，除非事先执行 `STORE_USER_ALL` |
| 恢复后输出状态 | 取决于 `OPERATION (0x01)` 和 `ON_OFF_CONFIG (0x02)` 的存储值，详见第 9 章 |

> **提示**：恢复顺序为 User Store → Default Store（User Store 优先级高于 Factory Default）。部分设备的 `RESTORE_DEFAULT_ALL` 不仅将 Factory Default 加载到 Operating Memory，还会同步覆盖 User Store，确保恢复出厂设置后下次上电不会从旧的用户配置启动。具体行为需参见产品 Datasheet。

---

*本附录为第 10 章（非易失性存储）的快速参考摘要。详细讲解、存储架构变体、写入次数限制等工程约束，以及 Host Driver 中的 NVM 策略配置，请参见第 10 章。*
