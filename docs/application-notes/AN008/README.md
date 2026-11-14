# AN008 — PMBus 应用手册（草稿）

> **文档状态：Draft / Pending Technical Review。** 本目录导入自用户提供的 `AN008.7z`，正文和附录保留原始 Markdown 内容，尚未完成产品适用性与命令语义审核。

## 定位

AN008 是面向系统工程师、固件工程师和 FAE 的 PMBus 应用手册，涵盖硬件接口、传输、数据编码、PEC、SMBALERT、状态/故障、控制与配置、NVM、遥测、启动、主机驱动和 Python 使用示例。

**它不是 PMBus 官方规范，也不是设备真实实现的权威来源。** 产品实际支持的命令、访问权限、默认值、数据编码和故障响应，以相应产品的 Datasheet、工程证据与 `examples/reference/*.pmbus.yaml`（并结合其源证据）为依据。

## 重要审核提示

归档随附的 [内容冲突审查报告](reviews/content_conflict_audit_report.md) 记录了多项未解决的技术矛盾，例如：

- NVM 指令码在不同章节出现 `STORE_DEFAULT_ALL=0x11` / `0x15`、`RESTORE_DEFAULT_ALL=0x12` / `0x16` 等不同表述；
- `ON_OFF_CONFIG` 的可写性与示例代码不一致；
- `STATUS_WORD` 低字节释义存在冲突；
- ARA 地址在部分章节写成 `0x0A`，其他章节写成 `0x0C`；
- NVM 存储模型、`CAPABILITY` 位定义及部分 Python 示例有待复核。

**不要将这些未审核内容直接用于固件命令实现、代码生成或合规性判断。** 导入操作没有修正文中的技术争议，也没有执行硬件测试。另见 [交叉引用审查报告](reviews/xref_audit_report.md)：两份报告的审核范围与结论并不相同，须分别阅读。

## 正文（16 章）

- [AN008_ch01_引言](chapters/AN008_ch01_引言.md)
- [AN008_ch02_PMBus协议基础](chapters/AN008_ch02_PMBus协议基础.md)
- [AN008_ch03_硬件接口设计](chapters/AN008_ch03_硬件接口设计.md)
- [AN008_ch04_PMBus传输协议](chapters/AN008_ch04_PMBus传输协议.md)
- [AN008_ch05_数据格式](chapters/AN008_ch05_数据格式.md)
- [AN008_ch06_包错误校验PEC](chapters/AN008_ch06_包错误校验PEC.md)
- [AN008_ch07_SMBALERT中断机制](chapters/AN008_ch07_SMBALERT中断机制.md)
- [AN008_ch08_状态监控与故障管理](chapters/AN008_ch08_状态监控与故障管理.md)
- [AN008_ch09_控制与配置命令](chapters/AN008_ch09_控制与配置命令.md)
- [AN008_ch10_非易失性存储](chapters/AN008_ch10_非易失性存储.md)
- [AN008_ch11_设备识别与信息命令](chapters/AN008_ch11_设备识别与信息命令.md)
- [AN008_ch12_遥测Telemetry](chapters/AN008_ch12_遥测Telemetry.md)
- [AN008_ch13_上电与启动行为](chapters/AN008_ch13_上电与启动行为.md)
- [AN008_ch14_主机端驱动开发指南](chapters/AN008_ch14_主机端驱动开发指南.md)
- [AN008_ch15_调试与故障排查](chapters/AN008_ch15_调试与故障排查.md)
- [AN008_ch16_Python编程示例](chapters/AN008_ch16_Python编程示例.md)

## 附录（11 篇）

- [AN008_appendix_A_完整命令列表](appendices/AN008_appendix_A_完整命令列表.md)
- [AN008_appendix_B_Linear快速参考](appendices/AN008_appendix_B_Linear快速参考.md)
- [AN008_appendix_C_CRC8查找表](appendices/AN008_appendix_C_CRC8查找表.md)
- [AN008_appendix_D_STATUS寄存器位域](appendices/AN008_appendix_D_STATUS寄存器位域.md)
- [AN008_appendix_E_FAULT_RESPONSE位域](appendices/AN008_appendix_E_FAULT_RESPONSE位域.md)
- [AN008_appendix_F_ONOFF行为摘要](appendices/AN008_appendix_F_ONOFF行为摘要.md)
- [AN008_appendix_G_NVM操作摘要](appendices/AN008_appendix_G_NVM操作摘要.md)
- [AN008_appendix_H_功能支持矩阵](appendices/AN008_appendix_H_功能支持矩阵.md)
- [AN008_appendix_I_FAQ](appendices/AN008_appendix_I_FAQ.md)
- [AN008_appendix_J_术语表](appendices/AN008_appendix_J_术语表.md)
- [AN008_appendix_K_参考文档索引](appendices/AN008_appendix_K_参考文档索引.md)

## 审查报告

- [content_conflict_audit_report](reviews/content_conflict_audit_report.md)
- [xref_audit_report](reviews/xref_audit_report.md)

## 写作资料

- [AN008_写作规范](editorial/AN008_写作规范.md)

## 公开发布与许可检查

当前仓库是公开仓库，原始 AN008 文件中未包含可独立验证的最终发布授权信息。正式合并前应确认这些文档可公开分发及相应的版权/许可范围；本目录不会因为结构验证通过就自动视为获准正式发布。

## 归档与维护原则

- 原始 Markdown 文件保留原文，不在导入 PR 中静默修复技术内容。
- `spec/` 是 PMBus IR 模型规范；本目录是应用文档草稿，不参与 Schema/semantic validator 的权威判定。
- 第 16 章 Python 示例为未独立验证的教学示例，不构成生产级驱动或硬件写操作的安全承诺。
- 内容与后续技术验证应通过独立 Issue/PR 修订，保留来源、修改理由与测试依据。
- 文档原始来源：`AN008.7z`（用户提供）。源文件未包含可以独立验证的正式发行批准声明，故不标为已发布的公司正式应用文档。

