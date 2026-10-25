# PMBus IR

<details>
<summary><div align="right"><strong>English</strong> | 简体中文</div></summary>

PMBus IR 是一种开放、厂商无关的中间表示（Intermediate Representation），用于精确描述一款电源设备实际实现的 PMBus 接口。

本项目定义一种规范化、机器可读的数据表示，可作为 PMBus 接口需求与相关工具的单一事实来源（single source of truth）。

## 为什么需要 PMBus IR？

PMBus 标准定义协议和命令语义，而产品数据手册、工程文档和固件实现通常采用不同且不一致的方式描述具体产品的接口。PMBus IR 在这些信息源与后续工程产物之间提供一个规范化的语义层。

```text
PMBus 标准
产品需求
数据手册
固件实现
        |
        v
     PMBus IR
        |
        +--> TRD 生成
        +--> 接口文档
        +--> 验证
        +--> 语义比较
        +--> 测试生成
        +--> 代码生成
```

PMBus IR 不是 PMBus 通信协议栈，也不用于重新定义或复制 PMBus 标准。PMBus 的规范性定义仍以官方标准为准。IR 只记录某一具体设备如何实现其 PMBus 接口。

## 核心概念

### PMBus IR Specification

定义 PMBus 接口应如何表示的语义模型与规则。

### PMBus IR Schema

用于验证 PMBus IR 文档的机器可读 Schema。

### PMBus IR Document

描述某一具体电源设备实际 PMBus 接口实现的实例文档。

文件名示例：

```text
example-module.pmbus.yaml
```

## 设计原则

1. **机器可读优先** —— YAML/JSON 是源表示；面向人的文档是由 IR 渲染得到的视图。
2. **厂商无关** —— 核心模型不能依赖某一家厂商的数据手册格式或命名习惯。
3. **描述语义，而不是表格** —— 不只记录命令或寄存器表，还要描述含义、约束、状态与行为。
4. **尽量无损** —— 模型应保留足够的信息，使工程师无需依赖隐藏假设即可理解和重建目标接口行为。
5. **可扩展** —— 必须能够表达厂商自定义命令和特殊行为，同时不破坏公共模型。
6. **可比较** —— 两款设备的接口应能够进行语义层面的比较，而不是仅比较 YAML 文本差异。

## 初始语义域

一份 PMBus IR 文档预计覆盖以下内容：

- 设备身份信息
- 所引用的标准版本
- 传输层与总线能力
- 地址、PAGE 与 rail 映射
- 命令与事务类型
- 数据表示与工程单位
- 遥测
- 配置与默认值
- 状态报告
- Fault 与 Warning
- 持久化行为
- 时序与行为
- 厂商自定义扩展

## 示例

```yaml
ir_version: "0.1"

device:
  manufacturer: Example Power
  model: EXAMPLE-DC-DC
  class: dc_dc_power_module

standards:
  pmbus: "1.5"

transport:
  interface: pmbus
  pec: supported
  max_bus_frequency_khz: 400

addressing:
  pages:
    - id: 0
      name: main_output

commands:
  READ_VOUT:
    code: 0x8B
    supported: true
    access: read_only
    transaction: read_word
    value:
      quantity: voltage
      unit: V
      encoding:
        type: linear16
        exponent_source: VOUT_MODE
    scope:
      pages: [0]
```

以上示例仅用于说明当前模型。v0.1 Schema 仍然有意保持不完整，因为现阶段需要通过真实设备实例逐步建立和冻结语义模型。

## 仓库结构

```text
pmbus-ir/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── spec/
│   ├── ir-model.md
│   ├── command-model.md
│   ├── data-model.md
│   ├── behavior-model.md
│   └── diff-semantics.md
├── schema/
│   └── pmbus-ir.schema.json
├── examples/
│   ├── minimal.pmbus.yaml
│   └── dc-dc-module.pmbus.yaml
├── tools/
│   └── README.md
└── tests/
    └── README.md
```

## v0.1 范围

第一阶段刻意保持较窄的范围：

- 定义 PMBus IR 的概念和边界；
- 定义第一版语义模型；
- 建立初始 JSON Schema；
- 建立至少一份较真实的 DC/DC reference document；
- 定义验证行为；
- 定义 semantic diff 行为。

GUI、PMBus master 实现、固件协议栈以及设备通信层均不属于 v0.1 范围。

## 当前状态

Early design / pre-v0.1。随着真实 reference device 的加入，模型和 Schema 预计仍会持续调整。

## License

Apache License 2.0。参见 [LICENSE](LICENSE)。

</details>

PMBus IR is an open, vendor-neutral intermediate representation for precisely describing the implemented PMBus interface of a power device.

The project defines a canonical, machine-readable representation that can serve as a single source of truth for PMBus interface requirements and tooling.

## Why PMBus IR?

PMBus specifications define protocol and command semantics, while product datasheets and engineering documents describe product-specific implementations in inconsistent forms. PMBus IR provides a normalized semantic layer between those sources and downstream engineering artifacts.

```text
PMBus specification
Product requirements
Datasheets
Firmware implementation
        |
        v
     PMBus IR
        |
        +--> TRD generation
        +--> Interface documentation
        +--> Validation
        +--> Semantic comparison
        +--> Test generation
        +--> Code generation
```

PMBus IR is not a PMBus communication stack and is not intended to reproduce the PMBus specification. Normative PMBus definitions remain with the official specification. The IR records how a particular device implements its PMBus interface.

## Core concepts

### PMBus IR Specification

The semantic model and rules that define how PMBus interfaces are represented.

### PMBus IR Schema

A machine-readable schema used to validate PMBus IR documents.

### PMBus IR Document

A concrete instance describing the implemented PMBus interface of a specific power device.

Example filename:

```text
example-module.pmbus.yaml
```

## Design principles

1. **Machine-readable first** — YAML/JSON is the source representation; human-readable documents are rendered views.
2. **Vendor-neutral** — the core model must not depend on one manufacturer's datasheet conventions.
3. **Semantic, not tabular** — describe meaning, constraints, state, and behavior rather than only command/register tables.
4. **Loss-minimizing** — the model should preserve enough information to reconstruct the intended interface behavior without hidden assumptions.
5. **Extensible** — manufacturer-specific commands and behaviors must be representable without weakening the common model.
6. **Diffable** — two device interfaces should be comparable semantically rather than by textual YAML differences.

## Initial semantic domains

A PMBus IR document is expected to cover these domains:

- device identity
- referenced standards
- transport and bus capabilities
- addressing, pages, and rails
- commands and transactions
- data representation and engineering units
- telemetry
- configuration and defaults
- status reporting
- faults and warnings
- persistence
- timing and behavior
- manufacturer-specific extensions

## Example

```yaml
ir_version: "0.1"

device:
  manufacturer: Example Power
  model: EXAMPLE-DC-DC
  class: dc_dc_power_module

standards:
  pmbus: "1.5"

transport:
  interface: pmbus
  pec: supported
  max_bus_frequency_khz: 400

addressing:
  pages:
    - id: 0
      name: main_output

commands:
  READ_VOUT:
    code: 0x8B
    supported: true
    access: read_only
    transaction: read_word
    value:
      quantity: voltage
      unit: V
      encoding:
        type: linear16
        exponent_source: VOUT_MODE
    scope:
      pages: [0]
```

This example is illustrative. The v0.1 schema is intentionally incomplete while the semantic model is being established from real device examples.

## Repository structure

```text
pmbus-ir/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── spec/
│   ├── ir-model.md
│   ├── command-model.md
│   ├── data-model.md
│   ├── behavior-model.md
│   └── diff-semantics.md
├── schema/
│   └── pmbus-ir.schema.json
├── examples/
│   ├── minimal.pmbus.yaml
│   └── dc-dc-module.pmbus.yaml
├── tools/
│   └── README.md
└── tests/
    └── README.md
```

## v0.1 scope

The first milestone is intentionally narrow:

- define the PMBus IR concept and boundaries;
- define the first semantic model;
- create an initial JSON Schema;
- build at least one realistic DC/DC reference document;
- define validation behavior;
- define semantic-diff behavior.

A GUI, PMBus master implementation, firmware stack, and device communication layer are out of scope for v0.1.

## Status

Early design / pre-v0.1. The model and schema are expected to change as reference devices are added.

## License

Apache License 2.0. See [LICENSE](LICENSE).
