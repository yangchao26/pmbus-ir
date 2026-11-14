# 附录 A 完整 PMBus 命令列表

> 本附录按功能分类列出 Omnion Power 数字电源模块支持的 PMBus 命令，供快速查阅。表格中的"支持情况"列标注命令在 Omnion Power 产品中的通用支持状态：标注"通用"表示大多数产品支持，标注"可选"或"如支持"表示部分产品支持。具体支持的命令以各产品 Datasheet 为准。

---

## A.1 系统命令

系统命令用于模块的 ON/OFF 控制、故障清除、写保护和存储管理等基础操作。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| OPERATION | 0x01 | R/W | Bit Field (1 Byte) | 输出 ON/OFF、裕量、关断行为控制 | 通用 |
| ON_OFF_CONFIG | 0x02 | R | Bit Field (1 Byte) | ON/OFF 引脚行为配置（极性、控制源等） | 通用 |
| CLEAR_FAULTS | 0x03 | W | — | 清除所有故障状态，释放 SMBALERT# | 通用 |
| WRITE_PROTECT | 0x10 | R/W | Bit Field (1 Byte) | PMBus 标准写保护等级设置 | 通用 |
| STORE_DEFAULT_ALL | 0x11 | W | — | 将运行参数存储到非易失性存储器（EEPROM） | 通用 |
| RESTORE_DEFAULT_ALL | 0x12 | W | — | 从非易失性存储器恢复所有配置到运行内存 | 通用 |
| PAGE | 0x00 | R/W | Byte | 多输出页选择（如支持） | 可选 |
| CAPABILITY | 0x19 | R | Bit Field (1 Byte) | 设备功能能力位域（PEC、SMBALERT、总线速率） | 通用 |

> ON/OFF 控制机制详见第 9 章。STORE_DEFAULT_ALL / RESTORE_DEFAULT_ALL 详见第 10 章。WRITE_PROTECT 详见第 9.6 节。

---

## A.2 设备信息命令

设备信息命令用于主机识别设备身份、协议兼容性和功能能力。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| PMBUS_REVISION | 0x98 | R | Bit Field (1 Byte) | PMBus 协议版本号（Part I + Part II） | 通用 |
| CAPABILITY | 0x19 | R | Bit Field (1 Byte) | 功能能力位域（PEC、SMBALERT、速率） | 通用 |
| QUERY | 0x9F | R | Byte（Receive Byte） | 快速能力查询，Bit 7 = PEC 支持 | 通用 |
| MFR_ID | 0x99 | R | Block（8-bit ASCII） | 厂商标识，Omnion Power 返回 "OMPW" | 通用 |
| MFR_MODEL | 0x9A | R | Block（8-bit ASCII） | 产品型号字符串 | 通用 |
| MFR_REVISION | 0x9B | R | Block（8-bit ASCII） | 硬件/固件版本字符串 | 通用 |
| MFR_LOCATION | 0x9C | R | Block（8-bit ASCII） | 制造地点 | 通用 |
| MFR_DATE | 0x9D | R | Block（8-bit ASCII） | 制造日期 | 通用 |
| MFR_SERIAL | 0x9E | R | Block（8-bit ASCII） | 产品唯一序列号 | 通用 |

> PMBUS_REVISION 的命令码是 **0x98**（不是 0x9A）。QUERY 使用 Receive Byte 传输类型，不发送命令码。详见第 11 章。

---

## A.3 输出电压命令

输出电压命令用于设定和调节模块输出电压。所有 VOUT 相关命令使用 VOUT Linear 数据格式，指数由 VOUT_MODE (0x20) 定义，通常为 -12（分辨率 0.244 mV）。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| VOUT_MODE | 0x20 | R | Mode + Exponent | VOUT 数据格式定义（模式 + 指数） | 通用 |
| VOUT_COMMAND | 0x21 | R/W | VOUT Linear | 输出电压设定点 | 通用 |
| VOUT_TRIM | 0x22 | R/W | Signed Fixed-Point | 输出电压微调偏移（叠加于 VOUT_COMMAND 之上） | 可选 |
| VOUT_CAL_OFFSET | 0x23 | R/W | VOUT Linear | VOUT 读数校准偏移（仅影响读数，不影响实际输出） | 通用 |
| VOUT_MAX | 0x24 | R/W | VOUT Linear | 输出电压最大允许值 | 可选 |
| VOUT_MARGIN_HIGH | 0x25 | R/W | VOUT Linear | 高裕量电压值 | 通用 |
| VOUT_MARGIN_LOW | 0x26 | R/W | VOUT Linear | 低裕量电压值 | 通用 |
| VOUT_DROOP | 0x28 | R/W | Linear（mV/A） | 输出电压下垂补偿（用于并联均流） | 通用 |
| VOUT_MIN | 0x2B | R/W | VOUT Linear | 输出电压最小允许值 | 可选 |

> VOUT Linear 格式的编码/解码方法详见第 5 章。裕量调节和 VOUT_COMMAND 详见第 9 章。

---

## A.4 遥测读取命令

遥测读取命令用于实时监测模块的运行参数。所有遥测命令使用 Read Word 传输类型。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| READ_VIN | 0x88 | R | Linear | 输入电压 | 通用 |
| READ_IIN | 0x89 | R | Linear | 输入电流 | 可选 |
| READ_VCAP | 0x8A | R | Linear | 外部电容电压 | 可选 |
| READ_VOUT | 0x8B | R | VOUT Linear | 输出电压 | 通用 |
| READ_IOUT | 0x8C | R | Linear | 输出电流 | 通用 |
| READ_TEMPERATURE_1 | 0x8D | R | Linear | 模块温度（主温度点） | 通用 |
| READ_TEMPERATURE_2 | 0x8E | R | Linear | 辅助温度点 2 | 可选 |
| READ_TEMPERATURE_3 | 0x8F | R | Linear | 辅助温度点 3 | 可选 |
| READ_POUT | 0x96 | R | Linear | 输出功率（内部计算） | 可选 |
| READ_PIN | 0x97 | R | Linear | 输入功率（内部计算） | 可选 |

> 遥测数据格式与精度详见第 12 章。READ_VOUT 使用 VOUT Linear（ULINEAR16）格式，其余命令使用 11-bit Linear 格式。

---

## A.5 保护阈值命令

保护阈值命令用于配置各类故障和警告的触发点。故障限制定义 Fault 级别保护的触发阈值，警告限制定义 Warning 级别的触发阈值。

### A.5.1 故障限制命令

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| VOUT_OV_FAULT_LIMIT | 0x40 | R/W | VOUT Linear | 输出过压故障阈值 | 通用 |
| VOUT_UV_FAULT_LIMIT | 0x43 | R/W | VOUT Linear | 输出欠压故障阈值 | 可选 |
| IOUT_OC_FAULT_LIMIT | 0x46 | R/W | Linear | 输出过流故障阈值 | 通用 |
| OT_FAULT_LIMIT | 0x4F | R/W | Linear | 过温故障阈值 | 通用 |
| VIN_OV_FAULT_LIMIT | 0x55 | R/W | Linear | 输入过压故障阈值 | 通用 |
| VIN_UV_FAULT_LIMIT | 0x59 | R/W | Linear | 输入欠压故障阈值 | 可选 |

### A.5.2 警告限制命令

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| VOUT_OV_WARN_LIMIT | 0x42 | R/W | VOUT Linear | 输出过压警告阈值 | 可选 |
| VOUT_UV_WARN_LIMIT | 0x44 | R/W | VOUT Linear | 输出欠压警告阈值 | 可选 |
| IOUT_OC_WARN_LIMIT | 0x4A | R/W | Linear | 输出过流警告阈值 | 通用 |
| IOUT_OC_LL_WARN_LIMIT | 0x4B | R/W | Linear | 输出低电流警告阈值 | 可选 |
| OT_WARN_LIMIT | 0x51 | R/W | Linear | 过温警告阈值 | 通用 |
| UT_WARN_LIMIT | 0x52 | R/W | Linear | 欠温警告阈值 | 可选 |
| VIN_UV_WARN_LIMIT | 0x5A | R/W | Linear | 输入欠压警告阈值 | 可选 |
| VIN_OV_WARN_LIMIT | 0x57 | R/W | Linear | 输入过压警告阈值 | 可选 |

> 保护阈值与 FAULT_RESPONSE 的交叉检查规则详见第 8 章。

---

## A.6 FAULT_RESPONSE 命令

FAULT_RESPONSE 命令定义各类故障触发后模块的行为（关断、重启策略、延迟时间），使用统一的 8-bit 位域结构。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| VOUT_OV_FAULT_RESPONSE | 0x41 | R/W | Bit Field (1 Byte) | 输出过压故障响应配置 | 通用 |
| VOUT_UV_FAULT_RESPONSE | 0x45 | R/W | Bit Field (1 Byte) | 输出欠压故障响应配置 | 可选 |
| IOUT_OC_FAULT_RESPONSE | 0x47 | R/W | Bit Field (1 Byte) | 输出过流故障响应配置 | 通用 |
| OT_FAULT_RESPONSE | 0x50 | R/W | Bit Field (1 Byte) | 过温故障响应配置 | 通用 |

FAULT_RESPONSE 位域结构：

| 位 | [7:6] | [5:3] | [2:0] |
|----|-------|-------|-------|
| 字段 | Response | Retry Setting | Delay Time |

> FAULT_RESPONSE 完整位域映射参见附录 E。各字段的取值含义详见第 8 章。

---

## A.7 时序配置命令

时序配置命令控制模块启动和关断过程中的时序参数，用于多电源系统的上电顺序控制。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| TON_DELAY | 0x60 | R/W | Linear（ms） | 启动延迟时间 | 通用 |
| TON_RISE | 0x61 | R/W | Linear（ms） | 输出电压上升时间 | 通用 |
| TOFF_DELAY | 0x64 | R/W | Linear（ms） | 关断延迟时间 | 可选 |
| TOFF_FALL | 0x65 | R/W | Linear（ms） | 输出电压下降时间 | 可选 |

> 关断时序命令（TOFF_DELAY / TOFF_FALL）仅在 OPERATION 命令 Bit 6（TOFF）= 1 时生效。时序配置详见第 9 章。

---

## A.8 PGOOD 配置命令

PGOOD 配置命令定义 Power Good 信号的有效窗口。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| POWER_GOOD_ON | 0x5E | R/W | VOUT Linear | PGOOD 断言阈值（输出电压高于此值时 PGOOD 有效） | 通用 |
| POWER_GOOD_OFF | 0x5F | R/W | VOUT Linear | PGOOD 取消断言阈值（输出电压低于此值时 PGOOD 无效） | 通用 |

> POWER_GOOD_ON 与 POWER_GOOD_OFF 之间必须保持至少 0.5V 的迟滞间距。PGOOD 极性可通过 MFR_PGOOD_POLARITY (0xE2) 配置。详见第 9 章。

---

## A.9 输入电压配置命令

输入电压配置命令通过迟滞门限控制模块在输入电源异常时的启停行为。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| VIN_ON | 0x35 | R/W | Linear（V） | 输入电压开启阈值（VIN 高于此值时允许启动） | 通用 |
| VIN_OFF | 0x36 | R/W | Linear（V） | 输入电压关闭阈值（VIN 低于此值时模块关闭） | 通用 |

> VIN_ON 与 VIN_OFF 之间必须保持至少 2V 的迟滞间距。详见第 9 章。

---

## A.10 状态寄存器命令

状态寄存器命令提供分层故障和警告监控能力。STATUS_WORD 作为概览入口，配合 5 个 STATUS_xxx 寄存器定位具体故障。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| STATUS_BYTE | 0x78 | R | Bit Field (1 Byte) | 8-bit 总体状态概览 | 通用 |
| STATUS_WORD | 0x79 | R | Bit Field (2 Byte) | 16-bit 扩展概览（STATUS_BYTE + STATUS_VOUT） | 通用 |
| STATUS_VOUT | 0x7A | R | Bit Field (1 Byte) | 输出电压状态 | 通用 |
| STATUS_IOUT | 0x7B | R | Bit Field (1 Byte) | 输出电流状态 | 通用 |
| STATUS_INPUT | 0x7C | R | Bit Field (1 Byte) | 输入电压状态 | 通用 |
| STATUS_TEMPERATURE | 0x7D | R | Bit Field (1 Byte) | 温度状态 | 通用 |
| STATUS_CML | 0x7E | R | Bit Field (1 Byte) | 通信 / 存储器 / 逻辑状态 | 通用 |
| STATUS_MFR_SPECIFIC | 0x80 | R | Bit Field (1 Byte) | 厂商特定状态 | 可选 |
| STATUS_FANS_1_2 | 0x81 | R | Bit Field (1 Byte) | 风扇 1/2 状态 | 可选 |
| STATUS_FANS_3_4 | 0x82 | R | Bit Field (1 Byte) | 风扇 3/4 状态 | 可选 |

> 状态寄存器位域定义详见第 8 章和附录 D。STATUS_WORD 是推荐的健康检查入口。

---

## A.11 SMBALERT_MASK 命令

SMBALERT_MASK 命令用于选择哪些故障/警告条件会触发 SMBALERT# 信号。对应 STATUS 寄存器的每一位，均有对应的 MASK 位控制是否产生 SMBALERT#。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| SMBALERT_MASK | 0x1B | R/W | Bit Field (1 Byte) | SMBALERT 总体掩码 | 如支持 |
| VOUT_OV_FAULT_MASK | 0x41（N/A） | — | — | — | — |
| SMBALERT_MASK_VOUT | 0x76 | R/W | Bit Field (1 Byte) | VOUT 类 SMBALERT 掩码 | 如支持 |
| SMBALERT_MASK_IOUT | 0x77 | R/W | Bit Field (1 Byte) | IOUT 类 SMBALERT 掩码 | 如支持 |
| SMBALERT_MASK_INPUT | 0x73 | R/W | Bit Field (1 Byte) | INPUT 类 SMBALERT 掩码 | 如支持 |
| SMBALERT_MASK_TEMPERATURE | 0x74 | R/W | Bit Field (1 Byte) | TEMPERATURE 类 SMBALERT 掩码 | 如支持 |
| SMBALERT_MASK_CML | 0x75 | R/W | Bit Field (1 Byte) | CML 类 SMBALERT 掩码 | 如支持 |

> SMBALERT 接口和 ARA 协议详见第 7 章。MASK 位为 0 表示该条件发生时触发 SMBALERT#，为 1 表示屏蔽。

---

## A.12 Store/Restore 命令

Store/Restore 命令用于运行参数的持久化保存与恢复。Omnion Power 产品采用单存储区模型，STORE_DEFAULT_ALL (0x11) 和 RESTORE_DEFAULT_ALL (0x12) 分别保存和恢复配置。

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| STORE_DEFAULT_ALL | 0x11 | W | — | 将运行参数保存到非易失性存储器（EEPROM） | 通用 |
| RESTORE_DEFAULT_ALL | 0x12 | W | — | 从非易失性存储器恢复所有配置 | 通用 |
| STORE_USER_ALL | 0x17 | W | — | 将运行参数保存到用户存储区（如支持） | 可选 |
| RESTORE_USER_ALL | 0x18 | W | — | 从用户存储区恢复配置（如支持） | 可选 |

> Store/Restore 操作详见第 10 章。STORE_DEFAULT_ALL 执行时间 ≤ 500ms，执行期间不应发送额外命令。

---

## A.13 MFR 厂商自定义命令

PMBus 规范在命令空间 0xC0 ~ 0xFF 预留了厂商专有命令区域。以下列出 Omnion Power 数字电源模块中常见的厂商自定义命令。

### A.13.1 命令空间

| 地址范围 | 用途 |
|----------|------|
| 0xC0 ~ 0xC3 | 保留（PMBus 规范预留） |
| 0xC4 ~ 0xFD | 厂商专有命令核心区域 |
| 0xFE ~ 0xFF | 保留（PMBus 规范预留） |

### A.13.2 已知 MFR 命令

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| MFR_DEVICE_TYPE | 0xD0 | R/W | 16-bit 自定义位域 | 写保护控制（WPE 位，Bit 1）及模块名称编码 | 通用 |
| MFR_FW_REV | 0xDB | R | 16-bit 无符号 | 固件版本（格式：0xMj.Mn.Bh.Bl） | 通用 |
| MFR_PGOOD_POLARITY | 0xE2 | R/W | Bit Field (1 Byte) | PGOOD 信号极性选择（Bit 0） | 通用 |
| MFR_MODULE_DATE_LOC_SN | 0xF0 | R/W | Block（12 Byte） | 模块日期、地点和序列号信息 | 通用 |

### A.13.3 常见 MFR 命令空间（产品相关）

以下命令在部分 Omnion Power 产品中可能出现，具体支持情况参见各产品 Datasheet：

| 命令名称 | 命令码 | 访问类型 | 数据格式 | 说明 | 支持情况 |
|----------|--------|----------|----------|------|----------|
| MFR_VIN_MIN | 0xC4 | R/W | Linear | 输入电压最小工作值 | 可选 |
| MFR_VOUT_MIN | 0xC5 | R/W | VOUT Linear | 输出电压最小值 | 可选 |
| MFR_IOUT_CAL_OFFSET | 0xCA | R/W | Linear | 输出电流校准偏移 | 可选 |
| MFR_BLACK_BOX_READ | 0xCE | R | Block | 黑盒故障记录读取 | 可选 |
| MFR_BLACK_BOX_CLEAR | 0xCF | W | — | 清除黑盒故障记录 | 可选 |

> 厂商自定义命令的具体行为和数据格式因产品而异。使用自定义命令前应参考具体产品 Datasheet。详见第 11 章。

---

## A.14 命令码速查索引

以下按命令码十六进制顺序排列，供快速检索。

| 命令码 | 命令名称 | 分类 | 访问类型 |
|--------|----------|------|----------|
| 0x00 | PAGE | 系统命令 | R/W |
| 0x01 | OPERATION | 系统命令 | R/W |
| 0x02 | ON_OFF_CONFIG | 系统命令 | R |
| 0x03 | CLEAR_FAULTS | 系统命令 | W |
| 0x10 | WRITE_PROTECT | 系统命令 | R/W |
| 0x11 | STORE_DEFAULT_ALL | Store/Restore | W |
| 0x12 | RESTORE_DEFAULT_ALL | Store/Restore | W |
| 0x17 | STORE_USER_ALL | Store/Restore | W |
| 0x18 | RESTORE_USER_ALL | Store/Restore | W |
| 0x19 | CAPABILITY | 设备信息 | R |
| 0x1B | SMBALERT_MASK | SMBALERT_MASK | R/W |
| 0x20 | VOUT_MODE | 输出电压 | R |
| 0x21 | VOUT_COMMAND | 输出电压 | R/W |
| 0x22 | VOUT_TRIM | 输出电压 | R/W |
| 0x23 | VOUT_CAL_OFFSET | 输出电压 | R/W |
| 0x24 | VOUT_MAX | 输出电压 | R/W |
| 0x25 | VOUT_MARGIN_HIGH | 输出电压 | R/W |
| 0x26 | VOUT_MARGIN_LOW | 输出电压 | R/W |
| 0x28 | VOUT_DROOP | 输出电压 | R/W |
| 0x2B | VOUT_MIN | 输出电压 | R/W |
| 0x35 | VIN_ON | 输入电压配置 | R/W |
| 0x36 | VIN_OFF | 输入电压配置 | R/W |
| 0x40 | VOUT_OV_FAULT_LIMIT | 保护阈值 | R/W |
| 0x41 | VOUT_OV_FAULT_RESPONSE | FAULT_RESPONSE | R/W |
| 0x42 | VOUT_OV_WARN_LIMIT | 保护阈值 | R/W |
| 0x43 | VOUT_UV_FAULT_LIMIT | 保护阈值 | R/W |
| 0x44 | VOUT_UV_WARN_LIMIT | 保护阈值 | R/W |
| 0x45 | VOUT_UV_FAULT_RESPONSE | FAULT_RESPONSE | R/W |
| 0x46 | IOUT_OC_FAULT_LIMIT | 保护阈值 | R/W |
| 0x47 | IOUT_OC_FAULT_RESPONSE | FAULT_RESPONSE | R/W |
| 0x4A | IOUT_OC_WARN_LIMIT | 保护阈值 | R/W |
| 0x4B | IOUT_OC_LL_WARN_LIMIT | 保护阈值 | R/W |
| 0x4F | OT_FAULT_LIMIT | 保护阈值 | R/W |
| 0x50 | OT_FAULT_RESPONSE | FAULT_RESPONSE | R/W |
| 0x51 | OT_WARN_LIMIT | 保护阈值 | R/W |
| 0x52 | UT_WARN_LIMIT | 保护阈值 | R/W |
| 0x55 | VIN_OV_FAULT_LIMIT | 保护阈值 | R/W |
| 0x57 | VIN_OV_WARN_LIMIT | 保护阈值 | R/W |
| 0x59 | VIN_UV_FAULT_LIMIT | 保护阈值 | R/W |
| 0x5A | VIN_UV_WARN_LIMIT | 保护阈值 | R/W |
| 0x5E | POWER_GOOD_ON | PGOOD 配置 | R/W |
| 0x5F | POWER_GOOD_OFF | PGOOD 配置 | R/W |
| 0x60 | TON_DELAY | 时序配置 | R/W |
| 0x61 | TON_RISE | 时序配置 | R/W |
| 0x64 | TOFF_DELAY | 时序配置 | R/W |
| 0x65 | TOFF_FALL | 时序配置 | R/W |
| 0x73 | SMBALERT_MASK_INPUT | SMBALERT_MASK | R/W |
| 0x74 | SMBALERT_MASK_TEMPERATURE | SMBALERT_MASK | R/W |
| 0x75 | SMBALERT_MASK_CML | SMBALERT_MASK | R/W |
| 0x76 | SMBALERT_MASK_VOUT | SMBALERT_MASK | R/W |
| 0x77 | SMBALERT_MASK_IOUT | SMBALERT_MASK | R/W |
| 0x78 | STATUS_BYTE | 状态寄存器 | R |
| 0x79 | STATUS_WORD | 状态寄存器 | R |
| 0x7A | STATUS_VOUT | 状态寄存器 | R |
| 0x7B | STATUS_IOUT | 状态寄存器 | R |
| 0x7C | STATUS_INPUT | 状态寄存器 | R |
| 0x7D | STATUS_TEMPERATURE | 状态寄存器 | R |
| 0x7E | STATUS_CML | 状态寄存器 | R |
| 0x80 | STATUS_MFR_SPECIFIC | 状态寄存器 | R |
| 0x81 | STATUS_FANS_1_2 | 状态寄存器 | R |
| 0x82 | STATUS_FANS_3_4 | 状态寄存器 | R |
| 0x88 | READ_VIN | 遥测读取 | R |
| 0x89 | READ_IIN | 遥测读取 | R |
| 0x8A | READ_VCAP | 遥测读取 | R |
| 0x8B | READ_VOUT | 遥测读取 | R |
| 0x8C | READ_IOUT | 遥测读取 | R |
| 0x8D | READ_TEMPERATURE_1 | 遥测读取 | R |
| 0x8E | READ_TEMPERATURE_2 | 遥测读取 | R |
| 0x8F | READ_TEMPERATURE_3 | 遥测读取 | R |
| 0x96 | READ_POUT | 遥测读取 | R |
| 0x97 | READ_PIN | 遥测读取 | R |
| 0x98 | PMBUS_REVISION | 设备信息 | R |
| 0x99 | MFR_ID | 设备信息 | R |
| 0x9A | MFR_MODEL | 设备信息 | R |
| 0x9B | MFR_REVISION | 设备信息 | R |
| 0x9C | MFR_LOCATION | 设备信息 | R |
| 0x9D | MFR_DATE | 设备信息 | R |
| 0x9E | MFR_SERIAL | 设备信息 | R |
| 0x9F | QUERY | 设备信息 | R |
| 0xC4 | MFR_VIN_MIN | MFR 自定义 | R/W |
| 0xC5 | MFR_VOUT_MIN | MFR 自定义 | R/W |
| 0xCA | MFR_IOUT_CAL_OFFSET | MFR 自定义 | R/W |
| 0xCE | MFR_BLACK_BOX_READ | MFR 自定义 | R |
| 0xCF | MFR_BLACK_BOX_CLEAR | MFR 自定义 | W |
| 0xD0 | MFR_DEVICE_TYPE | MFR 自定义 | R/W |
| 0xDB | MFR_FW_REV | MFR 自定义 | R |
| 0xE2 | MFR_PGOOD_POLARITY | MFR 自定义 | R/W |
| 0xF0 | MFR_MODULE_DATE_LOC_SN | MFR 自定义 | R/W |
