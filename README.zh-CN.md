# PMBus IR

<div align="right"><a href="./README.md">English</a> | <strong>简体中文</strong></div>

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
├── README.zh-CN.md
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
