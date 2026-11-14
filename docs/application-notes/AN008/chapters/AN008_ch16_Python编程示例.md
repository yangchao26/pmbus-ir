# 第 16 章 Python 编程示例

> 本章提供基于 Python + smbus2 库的完整编程示例，涵盖 PMBus 通信的环境搭建、基础读写、控制操作、PEC 校验、SMBALERT 中断处理和故障管理等实际开发场景。所有代码可直接使用，配有详细中文注释。

---

## 16.1 环境搭建

### 16.1.1 安装 smbus2 库

smbus2 是 Linux 上最常用的 SMBus/I2C Python 库。安装方式如下：

```bash
pip install smbus2
```

> **提示**: smbus2 依赖 Linux 内核的 I2C/SMBus 子系统（`/dev/i2c-*`），需要在 Linux 环境下运行。Windows 用户可通过 WSL（Windows Subsystem for Linux）或虚拟机使用。

安装完成后验证：

```python
import smbus2

# 列出系统中可用的 I2C 总线
import os
i2c_devices = [d for d in os.listdir('/dev') if d.startswith('i2c-')]
print(f"可用 I2C 总线: {i2c_devices}")
```

#### 系统权限配置

普通用户通常没有直接访问 I2C 设备节点的权限，需要配置 udev 规则或使用 sudo：

```bash
# 方法一：临时授权
sudo chmod 666 /dev/i2c-1

# 方法二：将用户加入 i2c 组（永久生效）
sudo groupadd -f i2c
sudo usermod -aG i2c $USER
# 创建 udev 规则
echo 'SUBSYSTEM=="i2c-dev", MODE="0666"' | sudo tee /etc/udev/rules.d/99-i2c.rules
sudo udevadm control --reload-rules
```

### 16.1.2 USB-to-I2C 适配器配置

在 PC 环境下进行 PMBus 开发时，通常需要 USB-to-I2C 适配器桥接。以下是常用适配器的配置要点：

#### 常见适配器对比

| 适配器 | 芯片 | Linux 支持 | 特点 |
|--------|------|-----------|------|
| FT232H | FTDI | libmpsse / pyftdi | 支持多种协议，速率灵活 |
| CH341A | WCH | i2c-ch341 内核驱动 | 低成本，即插即用 |
| Aardvark I2C/SPI | Total Phase | 官方 SDK | 功能全面，价格较高 |
| MCP2221 | Microchip | hid-mcp2221 内核驱动 | 自带上拉，体积小 |

#### 配置示例（以 CH341A 为例）

```bash
# 加载内核驱动
sudo modprobe i2c-dev

# 查看适配器是否被识别
ls /dev/i2c-*

# 使用 i2cdetect 扫描总线上的设备
sudo apt install i2c-tools
i2cdetect -y 1
# 输出示例：
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- 1a -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# ...
# 其中 1a 即为检测到的 PMBus 设备地址
```

#### 配置示例（以 MCP2221 为例）

```bash
# 安装内核驱动
sudo modprobe hid-mcp2221

# MCP2221 通常映射为 /dev/hidraw*，通过 i2c-dev 子系统暴露
# 确认映射关系
sudo dmesg | grep mcp2221

# 扫描总线
i2cdetect -y 0
```

> **提示**: 不同适配器的总线编号（bus number）不同。使用前应先确认适配器映射到哪个 `/dev/i2c-N` 节点，以及目标设备在该总线上的地址。

### 16.1.3 基础读写函数封装

以下代码封装了 PMBus 常用的传输类型操作，包括 Send Byte、Read Byte、R/W Byte、Read Word、R/W Word 和 Block Read。

数据格式说明详见第 5 章，传输协议详见第 4 章。

```python
"""
pmbus_base.py — PMBus 基础读写操作封装

基于 smbus2 库封装 PMBus 常用传输类型，支持错误处理和重试。
"""

import smbus2
import time
from typing import Optional, Tuple, List


class PMBusDevice:
    """PMBus 设备基础通信类"""

    def __init__(self, bus: int, addr: int, pec: bool = False):
        """
        初始化 PMBus 设备

        参数:
            bus: I2C 总线编号（对应 /dev/i2c-N 中的 N）
            addr: 7-bit 从设备地址
            pec:  是否启用 PEC 校验（默认关闭）
        """
        self.bus = bus
        self.addr = addr
        self.pec = pec
        self._bus = smbus2.SMBus(bus)
        self._retry_count = 3
        self._retry_delay = 0.05  # 重试间隔 50ms

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """关闭总线连接"""
        if self._bus is not None:
            self._bus.close()
            self._bus = None

    # ===== PMBus 传输类型封装 =====

    def send_byte(self, command: int) -> None:
        """
        Send Byte 传输：仅发送命令码，从设备无响应数据。

        适用命令：CLEAR_FAULTS、STORE_DEFAULT_ALL、RESTORE_DEFAULT_ALL 等。
        传输协议详见第 4 章。
        """
        for attempt in range(self._retry_count):
            try:
                self._bus.write_byte_data(self.addr, command, 0,
                                          force=self.pec)
                return
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Send Byte 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def read_byte(self, command: int) -> int:
        """
        Read Byte 传输：发送命令码后读取 1 字节数据。

        适用命令：STATUS_VOUT、STATUS_IOUT、CAPABILITY、PMBUS_REVISION 等。
        """
        for attempt in range(self._retry_count):
            try:
                data = self._bus.read_byte_data(self.addr, command,
                                                force=self.pec)
                return data
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Read Byte 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def write_byte(self, command: int, data: int) -> None:
        """
        Write Byte 传输：发送命令码 + 1 字节数据。

        适用命令：OPERATION、ON_OFF_CONFIG、WRITE_PROTECT 等。
        """
        for attempt in range(self._retry_count):
            try:
                self._bus.write_byte_data(self.addr, command, data,
                                          force=self.pec)
                return
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Write Byte 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def read_word(self, command: int) -> int:
        """
        Read Word 传输：发送命令码后读取 2 字节数据（低字节在前）。

        适用命令：READ_VOUT、READ_VIN、READ_IOUT、STATUS_WORD 等。
        返回值为已拼接的 16-bit 无符号整数。
        """
        for attempt in range(self._retry_count):
            try:
                data = self._bus.read_word_data(self.addr, command,
                                                force=self.pec)
                return data
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Read Word 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def write_word(self, command: int, data: int) -> None:
        """
        Write Word 传输：发送命令码 + 2 字节数据（低字节在前）。

        适用命令：VOUT_COMMAND、IOUT_OC_FAULT_LIMIT、OT_FAULT_LIMIT 等。
        """
        for attempt in range(self._retry_count):
            try:
                self._bus.write_word_data(self.addr, command, data,
                                          force=self.pec)
                return
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Write Word 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def read_block(self, command: int, max_length: int = 32) -> bytes:
        """
        Block Read 传输：发送命令码后读取 N+1 字节数据。

        第 1 字节为数据长度 N，后跟 N 字节数据。
        适用命令：MFR_ID、MFR_MODEL、MFR_SERIAL、MFR_DATE 等。

        参数:
            command: PMBus 命令码
            max_length: 最大期望读取字节数（含长度字节）

        返回:
            纯数据字节（不含长度前缀）
        """
        for attempt in range(self._retry_count):
            try:
                raw = self._bus.read_block_data(self.addr, command,
                                                force=self.pec)
                # smbus2 的 read_block_data 返回 list，首元素为长度
                length = raw[0]
                data = bytes(raw[1:1 + length])
                return data
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Block Read 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def write_block(self, command: int, data: bytes) -> None:
        """
        Block Write 传输：发送命令码 + 长度字节 + 数据字节。

        参数:
            command: PMBus 命令码
            data: 要写入的数据（自动添加长度前缀）
        """
        for attempt in range(self._retry_count):
            try:
                # smbus2 的 write_block_data 接受 list，首元素为长度
                payload = [len(data)] + list(data)
                self._bus.write_block_data(self.addr, command, payload,
                                           force=self.pec)
                return
            except (OSError, IOError) as e:
                if attempt == self._retry_count - 1:
                    raise RuntimeError(
                        f"Block Write 失败 (addr=0x{self.addr:02X}, "
                        f"cmd=0x{command:02X}): {e}"
                    ) from e
                time.sleep(self._retry_delay)

    def __repr__(self) -> str:
        return (f"PMBusDevice(bus={self.bus}, addr=0x{self.addr:02X}, "
                f"pec={self.pec})")
```

> **提示**: smbus2 的 `force` 参数控制是否在 I2C 事务中附加 PEC 字节。当 `force=True` 时，smbus2 会在写事务末尾发送 PEC，在读事务末尾验证 PEC。但 smbus2 内置的 PEC 实现可能不覆盖所有 SMBus PEC 计算范围（详见第 6 章），如需精确控制 PEC 计算，建议使用 16.4 节中的自定义 PEC 读写函数。

---

## 16.2 基础操作示例

### 16.2.1 读取 PMBUS_REVISION 和 CAPABILITY

PMBUS_REVISION 和 CAPABILITY 是设备发现阶段最优先读取的两个命令，用于确认设备支持的 PMBus 协议版本和功能特性。设备识别详见第 11 章。

```python
"""
read_device_info.py — 读取设备基本信息

演示如何读取 PMBUS_REVISION 和 CAPABILITY 命令，
确认设备协议版本和功能支持情况。
"""

from pmbus_base import PMBusDevice

# ===== PMBus 命令码定义 =====
CMD_CAPABILITY       = 0x19  # 能力寄存器
CMD_PMBUS_REVISION   = 0x98  # PMBus 协议版本

def read_capability(dev: PMBusDevice) -> dict:
    """
    读取并解析 CAPABILITY 寄存器

    CAPABILITY 位域定义:
      bit 7: SMBALERT 支持
      bit 6: 保留
      bit 5: 包错误校验 (PEC)
      bit 4: 保留
      bit 3: 最大总线速度
            0 = 100 kHz
            1 = 100 kHz 及 400 kHz
      bit 2: SMBus 命令 (MFR_SPECIFIC)
      bit 1: 制造商专用块
      bit 0: 制造商专用命令
    """
    raw = dev.read_byte(CMD_CAPABILITY)

    capability = {
        'raw': f'0x{raw:02X}',
        'smbalert_support': bool(raw & 0x80),
        'pec_support': bool(raw & 0x20),
        'max_bus_speed': '100/400 kHz' if (raw & 0x08) else '100 kHz',
    }
    return capability


def read_revision(dev: PMBusDevice) -> dict:
    """
    读取并解析 PMBUS_REVISION 寄存器

    格式:
      bits [7:5]: Part I 修订版本
      bit [4]:    保留
      bits [3:0]: Part II 修订版本
    """
    raw = dev.read_byte(CMD_PMBUS_REVISION)

    part1 = (raw >> 5) & 0x07
    part2 = raw & 0x0F

    revision = {
        'raw': f'0x{raw:02X}',
        'part_i_version': part1,
        'part_ii_version': part2,
    }
    return revision


def main():
    # 配置参数 — 根据实际硬件修改
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58  # 示例地址，需根据实际设备配置

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        print(f"设备: {dev}")
        print("-" * 40)

        # 读取 PMBUS_REVISION
        rev = read_revision(dev)
        print(f"PMBus 协议版本: Part I = {rev['part_i_version']}, "
              f"Part II = {rev['part_ii_version']}")
        print(f"  原始值: {rev['raw']}")

        # 读取 CAPABILITY
        cap = read_capability(dev)
        print(f"最大总线速率: {cap['max_bus_speed']}")
        print(f"SMBALERT 支持: {'是' if cap['smbalert_support'] else '否'}")
        print(f"PEC 支持: {'是' if cap['pec_support'] else '否'}")
        print(f"  原始值: {cap['raw']}")


if __name__ == '__main__':
    main()
```

### 16.2.2 读取制造商信息（MFR_ID / MFR_MODEL）

MFR_ID、MFR_MODEL 等标识命令使用 Block Read 传输类型返回 ASCII 字符串。设备标识命令详见第 11 章。

```python
"""
read_manufacturer_info.py — 读取制造商信息

演示如何通过 Block Read 传输读取设备标识字符串。
"""

from pmbus_base import PMBusDevice

# ===== 标识命令码定义 =====
CMD_MFR_ID          = 0x99  # 制造商 ID（Block Read）
CMD_MFR_MODEL       = 0x9A  # 产品型号（Block Read）
CMD_MFR_REVISION    = 0x9B  # 硬件修订版本（Block Read）
CMD_MFR_SERIAL      = 0x9E  # 序列号（Block Read）
CMD_MFR_DATE        = 0x9D  # 制造日期（Block Read）
CMD_MFR_FW_REV      = 0xDB  # 固件版本（Read Word，制造商特定命令）


def read_block_string(dev: PMBusDevice, command: int) -> str:
    """
    读取 Block Read 类型的字符串命令，返回解码后的 ASCII 字符串。

    PMBus Block Read 返回格式:
      [长度 N] [数据1] [数据2] ... [数据N]
    smbus2 已处理长度字节，此处直接解码返回的数据。
    """
    raw_data = dev.read_block(command)
    return raw_data.decode('ascii', errors='replace').strip()


def read_firmware_revision(dev: PMBusDevice) -> str:
    """
    读取固件版本（MFR_FW_REV）。

    MFR_FW_REV 使用 Read Word 传输，返回 4 个十六进制字符:
      0xMj.Mn.Bh.Bl（Major.Minor.BuildHigh.BuildLow）
    """
    raw = dev.read_word(CMD_MFR_FW_REV)
    major = (raw >> 12) & 0x0F
    minor = (raw >> 8) & 0x0F
    build_h = (raw >> 4) & 0x0F
    build_l = raw & 0x0F
    return f"{major}.{minor}.{build_h}{build_l}"


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        print("=== 设备标识信息 ===")
        print(f"MFR_ID:       {read_block_string(dev, CMD_MFR_ID)}")
        print(f"MFR_MODEL:    {read_block_string(dev, CMD_MFR_MODEL)}")
        print(f"MFR_REVISION: {read_block_string(dev, CMD_MFR_REVISION)}")
        print(f"MFR_DATE:     {read_block_string(dev, CMD_MFR_DATE)}")
        print(f"MFR_SERIAL:   {read_block_string(dev, CMD_MFR_SERIAL)}")
        print(f"固件版本:      {read_firmware_revision(dev)}")


if __name__ == '__main__':
    main()
```

### 16.2.3 读取遥测数据（VIN / VOUT / IOUT / Temperature）

遥测数据读取需要将 PMBus 线性格式（Linear11 / Linear16）解码为物理值。数据格式详解参见第 5 章，遥测命令详解参见第 12 章。

```python
"""
read_telemetry.py — 读取遥测数据

演示如何读取并解码 PMBus 遥测量。
包含 Linear11 和 Linear16 两种数据格式的解码函数。
"""

import struct
from pmbus_base import PMBusDevice

# ===== 遥测命令码定义 =====
CMD_VOUT_MODE         = 0x20  # VOUT 模式/指数
CMD_READ_VOUT         = 0x8B  # 读取输出电压（Linear16）
CMD_READ_VIN          = 0x88  # 读取输入电压（Linear11）
CMD_READ_IOUT         = 0x8C  # 读取输出电流（Linear11）
CMD_READ_TEMPERATURE_1 = 0x8D  # 读取温度（Linear11）


# ===== 数据格式解码函数 =====

def decode_vout_mode(raw: int) -> dict:
    """
    解析 VOUT_MODE 寄存器。

    格式:
      bits [7:5]: 模式（000 = 线性模式）
      bits [3:0]: 指数 N（二进制补码）
      实际指数 = -N

    返回:
        dict: 包含 mode 和 exponent 字段
    """
    mode = (raw >> 5) & 0x07
    n_raw = raw & 0x0F

    # N 为二进制补码，实际指数 = -N
    exponent = -n_raw

    mode_names = {0: 'Linear'}
    return {
        'raw': f'0x{raw:02X}',
        'mode': mode_names.get(mode, f'Unknown({mode})'),
        'exponent': exponent,
    }


def linear11_to_float(data_word: int) -> float:
    """
    将 Linear11 格式的 16-bit 数据字解码为浮点物理值。

    Linear11 结构（16 bit）:
      bits [15:11]: 5-bit 指数（二进制补码）
      bits [10:0]:  11-bit 尾数（二进制补码）

    计算公式: Value = mantissa × 2^(exponent)

    数据格式详解参见第 5 章。
    """
    # 提取指数（高 5 位）
    exponent_raw = (data_word >> 11) & 0x1F
    # 提取尾数（低 11 位）
    mantissa_raw = data_word & 0x7FF

    # 符号扩展：5-bit 二进制补码
    if exponent_raw & 0x10:
        exponent = exponent_raw - 32
    else:
        exponent = exponent_raw

    # 符号扩展：11-bit 二进制补码
    if mantissa_raw & 0x400:
        mantissa = mantissa_raw - 2048
    else:
        mantissa = mantissa_raw

    return mantissa * (2.0 ** exponent)


def linear16_to_float(data_word: int, exponent: int) -> float:
    """
    将 Linear16 格式的 16-bit 数据字解码为浮点物理值。

    Linear16 结构（16 bit）:
      bits [15:0]: 16-bit 无符号尾数

    计算公式: Value = mantissa × 2^(exponent)

    参数:
        data_word: 16-bit 无符号数据字
        exponent:  由 VOUT_MODE 指定的指数（如 -12）
    """
    return data_word * (2.0 ** exponent)


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        # 读取 VOUT_MODE 获取输出电压指数
        vout_mode_raw = dev.read_byte(CMD_VOUT_MODE)
        vout_mode = decode_vout_mode(vout_mode_raw)
        vout_exp = vout_mode['exponent']
        print(f"VOUT_MODE: {vout_mode['raw']} "
              f"(模式={vout_mode['mode']}, 指数={vout_exp})")
        print("-" * 40)

        # 读取输出电压（Linear16 格式）
        vout_raw = dev.read_word(CMD_READ_VOUT)
        vout = linear16_to_float(vout_raw, vout_exp)
        print(f"输出电压 (READ_VOUT):    {vout:.3f} V "
              f"(原始值: 0x{vout_raw:04X})")

        # 读取输入电压（Linear11 格式）
        vin_raw = dev.read_word(CMD_READ_VIN)
        vin = linear11_to_float(vin_raw)
        print(f"输入电压 (READ_VIN):     {vin:.3f} V "
              f"(原始值: 0x{vin_raw:04X})")

        # 读取输出电流（Linear11 格式）
        iout_raw = dev.read_word(CMD_READ_IOUT)
        iout = linear11_to_float(iout_raw)
        print(f"输出电流 (READ_IOUT):    {iout:.3f} A "
              f"(原始值: 0x{iout_raw:04X})")

        # 读取温度（Linear11 格式）
        temp_raw = dev.read_word(CMD_READ_TEMPERATURE_1)
        temp = linear11_to_float(temp_raw)
        print(f"模块温度 (READ_TEMPERATURE_1): {temp:.2f} °C "
              f"(原始值: 0x{temp_raw:04X})")


if __name__ == '__main__':
    main()
```

---

## 16.3 控制操作示例

### 16.3.1 设置输出电压（VOUT_COMMAND）

VOUT_COMMAND 使用 Linear16 格式设置输出电压设定值。电压编码需要根据 VOUT_MODE 中的指数将物理电压值转换为 16-bit 无符号尾数。ON/OFF 控制详见第 9 章。

```python
"""
set_vout_command.py — 设置输出电压

演示如何将物理电压值编码为 PMBus Linear16 格式并写入 VOUT_COMMAND。
"""

from pmbus_base import PMBusDevice

# ===== 命令码定义 =====
CMD_VOUT_MODE    = 0x20  # VOUT 模式/指数
CMD_VOUT_COMMAND = 0x21  # 输出电压设定值


def encode_linear16(voltage: float, exponent: int) -> int:
    """
    将物理电压值编码为 Linear16 格式的 16-bit 数据字。

    计算公式: 尾数 = 电压值 / 2^(指数)

    参数:
        voltage:  目标电压值（V）
        exponent: VOUT_MODE 指定的指数（通常为 -12）

    返回:
        16-bit 无符号整数
    """
    mantissa = round(voltage / (2.0 ** exponent))

    # 检查范围（16-bit 无符号）
    if mantissa < 0 or mantissa > 0xFFFF:
        raise ValueError(
            f"电压 {voltage} V 超出编码范围 "
            f"(尾数 0x{mantissa:04X} 超出 16-bit 无符号范围)"
        )

    return mantissa


def set_vout(dev: PMBusDevice, voltage: float) -> None:
    """
    设置输出电压设定值。

    步骤:
      1. 读取 VOUT_MODE 获取指数
      2. 将目标电压编码为 Linear16 数据字
      3. 写入 VOUT_COMMAND
    """
    # 读取 VOUT_MODE
    vout_mode_raw = dev.read_byte(CMD_VOUT_MODE)
    exponent = -(vout_mode_raw & 0x0F)

    # 编码目标电压
    data_word = encode_linear16(voltage, exponent)

    # 写入 VOUT_COMMAND
    dev.write_word(CMD_VOUT_COMMAND, data_word)
    print(f"已设置输出电压: {voltage:.3f} V "
          f"(数据字: 0x{data_word:04X}, 指数: {exponent})")


def get_vout(dev: PMBusDevice) -> float:
    """读取当前输出电压设定值（VOUT_COMMAND）"""
    vout_mode_raw = dev.read_byte(CMD_VOUT_MODE)
    exponent = -(vout_mode_raw & 0x0F)
    data_word = dev.read_word(CMD_VOUT_COMMAND)
    return data_word * (2.0 ** exponent)


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        # 读取当前设定值
        current = get_vout(dev)
        print(f"当前 VOUT_COMMAND: {current:.3f} V")

        # 设置新的输出电压（注意：需确认目标值在允许范围内）
        target_voltage = 11.400  # 示例值，需根据实际产品调整
        set_vout(dev, target_voltage)

        # 回读验证
        new_vout = get_vout(dev)
        print(f"回读 VOUT_COMMAND: {new_vout:.3f} V")


if __name__ == '__main__':
    main()
```

> **提示**: 修改 VOUT_COMMAND 等受保护的参数前，需要先关闭写保护（WRITE_PROTECT）。写保护机制详见第 9 章。此外，VOUT_OV_FAULT_LIMIT 必须大于 VOUT_COMMAND，否则设备可能拒绝写入或自动覆盖，保护阈值交叉检查规则详见第 8 章。

### 16.3.2 软件关断与开启（OPERATION）

OPERATION 命令用于通过 PMBus 总线控制模块的输出开关。ON_OFF_CONFIG 命令决定模块是否响应 OPERATION 命令的 ON/OFF 控制。控制与配置命令详见第 9 章。

```python
"""
control_on_off.py — 软件关断与开启

演示如何使用 OPERATION 命令控制模块输出，
以及如何配置 ON_OFF_CONFIG 使模块响应总线控制。
"""

from pmbus_base import PMBusDevice

# ===== 命令码定义 =====
CMD_OPERATION      = 0x01  # 操作命令
CMD_ON_OFF_CONFIG  = 0x02  # ON/OFF 配置
CMD_STATUS_WORD    = 0x79  # 状态字


def read_on_off_config(dev: PMBusDevice) -> dict:
    """
    读取并解析 ON_OFF_CONFIG 寄存器。

    ON_OFF_CONFIG 位域定义（参见第 9 章）:
      bit 4: DEFAULT    — 上电默认行为
      bit 3: OPERATION  — 是否响应 OPERATION 命令
      bit 2: CONTROL    — 是否响应 CONTROL 引脚
      bit 1: POLARITY   — CONTROL 引脚极性
      bit 0: ACTION     — 关断动作（立即/延时）
    """
    raw = dev.read_byte(CMD_ON_OFF_CONFIG)
    return {
        'raw': f'0x{raw:02X}',
        'default_on_powerup': bool(raw & 0x10),
        'responds_to_operation': bool(raw & 0x08),
        'responds_to_control_pin': bool(raw & 0x04),
        'control_pin_polarity': 'Active High' if (raw & 0x02) else 'Active Low',
        'turn_off_action': 'Immediate' if (raw & 0x01) else 'Programmed delay',
    }


def ensure_operation_control(dev: PMBusDevice) -> None:
    """
    确保 ON_OFF_CONFIG 中 OPERATION 位（bit 3）被置位，
    使模块响应总线 ON/OFF 命令。
    """
    raw = dev.read_byte(CMD_ON_OFF_CONFIG)

    if not (raw & 0x08):
        # 置位 OPERATION 位
        new_val = raw | 0x08
        dev.write_byte(CMD_ON_OFF_CONFIG, new_val)
        print(f"已启用 OPERATION 总线控制 "
              f"(0x{raw:02X} → 0x{new_val:02X})")
    else:
        print("OPERATION 总线控制已启用")


def turn_on(dev: PMBusDevice) -> None:
    """
    通过 OPERATION 命令开启模块输出。

    OPERATION 位域:
      bit 7: ON/OFF（1=开, 0=关）
    """
    # 读取当前 OPERATION 值，保留其他位
    current = dev.read_byte(CMD_OPERATION)
    new_val = current | 0x80  # 置位 ON/OFF 位
    dev.write_byte(CMD_OPERATION, new_val)
    print(f"模块输出已开启 (OPERATION: 0x{current:02X} → 0x{new_val:02X})")


def turn_off(dev: PMBusDevice) -> None:
    """
    通过 OPERATION 命令关闭模块输出。

    注意: 关闭操作会立即停止输出。如需按设定的 TOFF_DELAY/TOFF_FALL
    时序关断，需配置 OPERATION bit 6（TOFF），具体参见第 9 章。
    """
    current = dev.read_byte(CMD_OPERATION)
    new_val = current & 0x7F  # 清除 ON/OFF 位
    dev.write_byte(CMD_OPERATION, new_val)
    print(f"模块输出已关闭 (OPERATION: 0x{current:02X} → 0x{new_val:02X})")


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        # 查看 ON_OFF_CONFIG
        config = read_on_off_config(dev)
        print("当前 ON_OFF_CONFIG:")
        for k, v in config.items():
            print(f"  {k}: {v}")
        print("-" * 40)

        # 确保模块响应总线控制
        ensure_operation_control(dev)
        print("-" * 40)

        # 关闭输出
        turn_off(dev)

        # 等待确认
        status = dev.read_word(CMD_STATUS_WORD)
        off_flag = bool(status & 0x0040)  # bit 6 = OFF
        print(f"确认 STATUS_WORD bit 6 (OFF): {off_flag}")

        # 重新开启
        turn_on(dev)

        status = dev.read_word(CMD_STATUS_WORD)
        off_flag = bool(status & 0x0040)
        print(f"确认 STATUS_WORD bit 6 (OFF): {off_flag}")


if __name__ == '__main__':
    main()
```

### 16.3.3 裕量调节测试

裕量调节（Margining）用于测试电源输出电压的容忍范围。通过 OPERATION 命令的 bits[5:4] 选择不同的电压设定值来源。裕量调节详见第 9 章。

```python
"""
margin_test.py — 裕量调节测试

演示如何通过 OPERATION 命令在标称值、高裕量和低裕量之间切换，
用于系统级别的电源裕量测试。
"""

import time
from pmbus_base import PMBusDevice

# ===== 命令码定义 =====
CMD_OPERATION         = 0x01
CMD_VOUT_COMMAND      = 0x21
CMD_VOUT_MARGIN_HIGH  = 0x25  # 高裕量电压设定值
CMD_VOUT_MARGIN_LOW   = 0x26  # 低裕量电压设定值
CMD_READ_VOUT         = 0x8B
CMD_VOUT_MODE         = 0x20

# OPERATION 命令中裕量控制位
# bits [5:4]:
#   00 = VOUT_COMMAND（标称值）
#   01 = VOUT_MARGIN_HIGH
#   10 = VOUT_MARGIN_LOW
#   11 = AVSBus（如支持）
# bits [3:2]:
#   01 = 裕量故障被忽略（Ignore Faults）
#   10 = 裕量故障被响应（Act on Fault）
MARGIN_NOMINAL     = 0x00  # bits[5:4] = 00
MARGIN_HIGH        = 0x20  # bits[5:4] = 01
MARGIN_LOW         = 0x40  # bits[5:4] = 10
MARGIN_ACT_ON_FAULT = 0x08  # bits[3:2] = 10


def set_margin(dev: PMBusDevice, mode: int) -> None:
    """
    设置裕量模式。

    参数:
        mode: 裕量模式（MARGIN_NOMINAL / MARGIN_HIGH / MARGIN_LOW）
    """
    # 读取当前值，保留 ON/OFF 位（bit 7），设置裕量位和故障响应位
    current = dev.read_byte(CMD_OPERATION)
    # 保持 bit 7（ON/OFF），清除 bits[5:2]，设置新的裕量模式和故障响应
    new_val = (current & 0x80) | mode | MARGIN_ACT_ON_FAULT
    dev.write_byte(CMD_OPERATION, new_val)

    mode_names = {
        MARGIN_NOMINAL: '标称 (VOUT_COMMAND)',
        MARGIN_HIGH: '高裕量 (VOUT_MARGIN_HIGH)',
        MARGIN_LOW: '低裕量 (VOUT_MARGIN_LOW)',
    }
    print(f"已切换至: {mode_names.get(mode, '未知模式')} "
          f"(OPERATION: 0x{new_val:02X})")


def read_actual_vout(dev: PMBusDevice) -> float:
    """读取实际输出电压"""
    vout_mode_raw = dev.read_byte(CMD_VOUT_MODE)
    exponent = -(vout_mode_raw & 0x0F)
    data_word = dev.read_word(CMD_READ_VOUT)
    return data_word * (2.0 ** exponent)


def margin_test_cycle(dev: PMBusDevice, settle_time: float = 0.5) -> None:
    """
    执行一次完整的裕量测试循环。

    步骤:
      1. 标称模式 → 读取 VOUT
      2. 高裕量 → 读取 VOUT
      3. 低裕量 → 读取 VOUT
      4. 恢复标称

    参数:
        settle_time: 每次切换后的稳定等待时间（秒）
    """
    modes = [
        (MARGIN_NOMINAL, '标称'),
        (MARGIN_HIGH, '高裕量'),
        (MARGIN_LOW, '低裕量'),
        (MARGIN_NOMINAL, '恢复标称'),
    ]

    for mode, label in modes:
        set_margin(dev, mode)
        time.sleep(settle_time)
        vout = read_actual_vout(dev)
        print(f"  → {label}: 实际输出 = {vout:.3f} V")


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        print("=== 裕量调节测试 ===")
        print("-" * 40)

        # 读取裕量设定值
        vout_mode_raw = dev.read_byte(CMD_VOUT_MODE)
        exponent = -(vout_mode_raw & 0x0F)

        def decode_vout(raw):
            return raw * (2.0 ** exponent)

        cmd = dev.read_word(CMD_VOUT_COMMAND)
        high = dev.read_word(CMD_VOUT_MARGIN_HIGH)
        low = dev.read_word(CMD_VOUT_MARGIN_LOW)
        print(f"VOUT_COMMAND:      {decode_vout(cmd):.3f} V")
        print(f"VOUT_MARGIN_HIGH:  {decode_vout(high):.3f} V")
        print(f"VOUT_MARGIN_LOW:   {decode_vout(low):.3f} V")
        print("-" * 40)

        # 执行裕量测试循环
        margin_test_cycle(dev)


if __name__ == '__main__':
    main()
```

> **提示**: 裕量切换时，输出电压需要一定的建立时间。`settle_time` 应根据实际应用的负载响应特性调整。裕量测试期间，模块会对超过 VOUT_OV_FAULT_LIMIT 的裕量高值触发过压保护，因此 VOUT_MARGIN_HIGH 应在保护阈值以内。

---

## 16.4 PEC 计算与验证

PEC（Packet Error Check, PEC）是 SMBus 定义的数据完整性校验机制，使用 CRC-8 算法。PEC 的计算方法、计算范围和校验流程详见第 6 章。

### 16.4.1 CRC-8 直接计算函数

以下实现使用 CRC-8 多项式 `0x07`（x^8 + x^2 + x + 1），初始值为 0x00，无反射、无 final XOR。

```python
"""
crc8_direct.py — CRC-8 直接计算实现

实现 SMBus/PMBus 规范中定义的 CRC-8 校验算法。
多项式: 0x07 (x^8 + x^2 + x + 1)
初始值: 0x00
无反射、无 final XOR

PEC 算法原理参见第 6 章。
"""


def crc8(data: bytes) -> int:
    """
    计算一字节数据的 CRC-8 校验值。

    参数:
        data: 参与计算的字节序列

    返回:
        8-bit CRC 校验值（0x00 ~ 0xFF）
    """
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def pec_calculate_read_word(addr: int, command: int,
                            data_low: int, data_high: int) -> int:
    """
    计算 Read Word 事务的 PEC 值。

    PEC 计算范围（参见第 6 章）:
      [地址+W] [命令] [地址+R] [数据低字节] [数据高字节]

    参数:
        addr:      7-bit 从设备地址
        command:   PMBus 命令码
        data_low:  返回数据的低字节
        data_high: 返回数据的高字节

    返回:
        PEC 字节

    示例验证（取自 SMBus 规范示例）:
      addr=0x5A, cmd=0x8B, data=0x00 0x30
      参与计算: 0xB4 0x8B 0xB5 0x00 0x30
      PEC = 0x4F
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
        (addr << 1) | 0x01,  # 地址 + Read bit
        data_low,              # 数据低字节
        data_high,             # 数据高字节
    ])
    return crc8(packet)


def pec_calculate_write_word(addr: int, command: int,
                             data_low: int, data_high: int) -> int:
    """
    计算 Write Word 事务的 PEC 值。

    PEC 计算范围:
      [地址+W] [命令] [数据低字节] [数据高字节]
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
        data_low,              # 数据低字节
        data_high,             # 数据高字节
    ])
    return crc8(packet)


def pec_calculate_send_byte(addr: int, command: int) -> int:
    """
    计算 Send Byte 事务的 PEC 值。

    PEC 计算范围:
      [地址+W] [命令]
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
    ])
    return crc8(packet)


def pec_calculate_write_byte(addr: int, command: int, data: int) -> int:
    """
    计算 Write Byte 事务的 PEC 值。

    PEC 计算范围:
      [地址+W] [命令] [数据]
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
        data,                  # 数据字节
    ])
    return crc8(packet)


def pec_calculate_read_byte(addr: int, command: int, data: int) -> int:
    """
    计算 Read Byte 事务的 PEC 值。

    PEC 计算范围:
      [地址+W] [命令] [地址+R] [数据]
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
        (addr << 1) | 0x01,  # 地址 + Read bit
        data,                  # 数据字节
    ])
    return crc8(packet)


def pec_calculate_read_block(addr: int, command: int,
                             data: bytes) -> int:
    """
    计算 Block Read 事务的 PEC 值。

    PEC 计算范围:
      [地址+W] [命令] [地址+R] [长度N] [数据1] [数据2] ... [数据N]
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
        (addr << 1) | 0x01,  # 地址 + Read bit
        len(data),             # 长度字节
    ]) + data
    return crc8(packet)


def pec_calculate_write_block(addr: int, command: int,
                              data: bytes) -> int:
    """
    计算 Block Write 事务的 PEC 值。

    PEC 计算范围:
      [地址+W] [命令] [长度N] [数据1] [数据2] ... [数据N]
    """
    packet = bytes([
        (addr << 1) | 0x00,  # 地址 + Write bit
        command,               # 命令码
        len(data),             # 长度字节
    ]) + data
    return crc8(packet)


# ===== 自测试 =====

if __name__ == '__main__':
    # 验证 SMBus 规范中的示例
    # 地址=0x5A, 命令=READ_VOUT(0x8B), 返回数据=0x00 0x30
    pec = pec_calculate_read_word(0x5A, 0x8B, 0x00, 0x30)
    assert pec == 0x4F, f"PEC 计算错误: 期望 0x4F, 实际 0x{pec:02X}"
    print(f"Read Word PEC 验证通过: 0x{pec:02X}")

    # 逐字节 CRC 验证（取自第 6 章示例）
    test_data = bytes([0xB4, 0x8B, 0xB5, 0x00, 0x30])
    pec_step = crc8(test_data)
    assert pec_step == 0x4F, f"逐步 CRC 错误: 0x{pec_step:02X}"
    print(f"逐步 CRC 验证通过: 0x{pec_step:02X}")
```

### 16.4.2 CRC-8 查表法实现

查表法通过预计算 256 字节的 CRC 查找表，将每个字节的 CRC 计算简化为一次异或和一次查表操作，显著提升计算速度。

```python
"""
crc8_table.py — CRC-8 查表法实现

提供完整的 256 字节 CRC-8 查找表和查表计算函数。
适用于需要频繁计算 PEC 的场景（如实时轮询系统）。
"""


def _generate_crc8_table() -> list:
    """
    生成 CRC-8 查找表。

    多项式: 0x07 (x^8 + x^2 + x + 1)
    初始值: 0x00

    表的每一项对应一个输入字节在 CRC=0 时的 CRC 结果。
    """
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
        table.append(crc)
    return table


# 生成完整的 256 字节 CRC-8 查找表
CRC8_TABLE = _generate_crc8_table()


def crc8_table(data: bytes) -> int:
    """
    使用查表法计算 CRC-8。

    参数:
        data: 参与计算的字节序列

    返回:
        8-bit CRC 校验值
    """
    crc = 0x00
    for byte in data:
        crc = CRC8_TABLE[crc ^ byte]
    return crc


def print_crc8_table() -> None:
    """打印完整的 CRC-8 查找表（用于验证或嵌入固件）"""
    print("CRC-8 查找表（多项式 0x07）:")
    print()
    for row in range(16):
        offset = row * 16
        hex_vals = ' '.join(f'0x{v:02X}' for v in CRC8_TABLE[offset:offset + 16])
        print(f"  {hex_vals}")


# ===== 自测试 =====

if __name__ == '__main__':
    # 验证查表法与直接计算法结果一致
    test_vectors = [
        bytes([0xB4, 0x8B, 0xB5, 0x00, 0x30]),  # Read Word 示例，期望 0x4F
        bytes([0xB4, 0x8B]),                       # 部分数据
        bytes([0x00, 0x00, 0x00, 0x00, 0x00]),     # 全零
        bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF]),     # 全一
    ]

    from crc8_direct import crc8 as crc8_direct

    for i, vec in enumerate(test_vectors):
        direct_result = crc8_direct(vec)
        table_result = crc8_table(vec)
        assert direct_result == table_result, (
            f"测试向量 {i} 不一致: "
            f"直接法=0x{direct_result:02X}, 查表法=0x{table_result:02X}"
        )
        print(f"测试向量 {i} 通过: CRC = 0x{table_result:02X}")

    # 打印查找表
    print()
    print_crc8_table()
```

### 16.4.3 带 PEC 的读写操作

smbus2 库内置了 PEC 支持（通过 `force=True`），但其 PEC 计算范围可能与 SMBus 规范不完全一致。以下示例展示如何通过原始 I2C 读写实现精确的 PEC 控制。

```python
"""
pmbus_pec_io.py — 带 PEC 的 PMBus 读写操作

通过 smbus2 的 raw I2C 操作实现精确的 PEC 控制。
适用于需要自行计算和验证 PEC 的场景。
PEC 原理和计算范围参见第 6 章。
"""

import smbus2
import struct
from crc8_table import crc8_table


class PMBusPECDevice:
    """
    带 PEC 校验的 PMBus 设备通信类。

    所有读写操作自动计算和验证 PEC。
    """

    def __init__(self, bus: int, addr: int):
        self.bus_num = bus
        self.addr = addr
        self._bus = smbus2.SMBus(bus)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self._bus is not None:
            self._bus.close()
            self._bus = None

    def _addr_w(self) -> int:
        """7-bit 地址 + Write bit"""
        return (self.addr << 1) | 0x00

    def _addr_r(self) -> int:
        """7-bit 地址 + Read bit"""
        return (self.addr << 1) | 0x01

    def read_byte_pec(self, command: int) -> tuple:
        """
        带校验的 Read Byte 操作。

        返回:
            (data_byte, pec_valid) — 数据字节和 PEC 校验是否通过
        """
        # 写阶段：发送地址+W 和命令
        self._bus.write_byte(self.addr, command)

        # 读阶段：读取 2 字节（1 数据 + 1 PEC）
        # 使用 I2C read_i2c_block_data 读取
        raw = self._bus.read_i2c_block_data(self.addr, command, 2)

        data = raw[0]
        pec_received = raw[1]

        # 计算 PEC: [地址+W] [命令] [地址+R] [数据]
        pec_calc = crc8_table(bytes([
            self._addr_w(),
            command,
            self._addr_r(),
            data,
        ]))

        return data, (pec_calc == pec_received)

    def read_word_pec(self, command: int) -> tuple:
        """
        带校验的 Read Word 操作。

        返回:
            (data_word, pec_valid) — 16-bit 数据字和 PEC 校验是否通过
        """
        # 写阶段
        self._bus.write_byte(self.addr, command)

        # 读阶段：读取 3 字节（2 数据 + 1 PEC）
        raw = self._bus.read_i2c_block_data(self.addr, command, 3)

        data_low = raw[0]
        data_high = raw[1]
        pec_received = raw[2]

        # 组合数据字（低字节在前）
        data_word = (data_high << 8) | data_low

        # 计算 PEC
        pec_calc = crc8_table(bytes([
            self._addr_w(),
            command,
            self._addr_r(),
            data_low,
            data_high,
        ]))

        return data_word, (pec_calc == pec_received)

    def write_byte_pec(self, command: int, data: int) -> None:
        """
        带校验的 Write Byte 操作。

        计算 PEC 并附加在写入数据的末尾。
        """
        pec = crc8_table(bytes([
            self._addr_w(),
            command,
            data,
        ]))

        # 使用 write_i2c_block_data 写入：[命令] [数据] [PEC]
        self._bus.write_i2c_block_data(self.addr, command, [data, pec])

    def write_word_pec(self, command: int, data_word: int) -> None:
        """
        带校验的 Write Word 操作。

        参数:
            data_word: 16-bit 数据（函数内部处理高低字节顺序）
        """
        data_low = data_word & 0xFF
        data_high = (data_word >> 8) & 0xFF

        pec = crc8_table(bytes([
            self._addr_w(),
            command,
            data_low,
            data_high,
        ]))

        # 写入：[命令] [低字节] [高字节] [PEC]
        self._bus.write_i2c_block_data(
            self.addr, command,
            [data_low, data_high, pec]
        )

    def send_byte_pec(self, command: int) -> None:
        """
        带校验的 Send Byte 操作。

        计算 PEC 并附加在命令码之后发送。
        """
        pec = crc8_table(bytes([
            self._addr_w(),
            command,
        ]))

        self._bus.write_i2c_block_data(self.addr, command, [pec])

    def read_block_pec(self, command: int) -> tuple:
        """
        带校验的 Block Read 操作。

        返回:
            (data_bytes, pec_valid) — 数据字节列表和 PEC 校验是否通过
        """
        # 先读取长度字节确定数据量
        # Block Read: [长度N] [数据1] ... [数据N] [PEC]
        # 最多读取 33 字节（32 数据 + 1 PEC）
        raw = self._bus.read_i2c_block_data(self.addr, command, 33)

        length = raw[0]
        data = bytes(raw[1:1 + length])
        pec_received = raw[1 + length]

        # 计算 PEC
        pec_calc = crc8_table(bytes([
            self._addr_w(),
            command,
            self._addr_r(),
            length,
        ]) + data)

        return data, (pec_calc == pec_received)


def main():
    """
    PEC 读写操作演示。
    """
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusPECDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        # Read Word + PEC 校验
        CMD_READ_VOUT = 0x8B
        data, pec_ok = dev.read_word_pec(CMD_READ_VOUT)
        print(f"READ_VOUT: 0x{data:04X}, PEC 校验: "
              f"{'通过' if pec_ok else '失败'}")

        # Read Byte + PEC 校验
        CMD_CAPABILITY = 0x19
        data, pec_ok = dev.read_byte_pec(CMD_CAPABILITY)
        print(f"CAPABILITY: 0x{data:02X}, PEC 校验: "
              f"{'通过' if pec_ok else '失败'}")

        # Block Read + PEC 校验
        CMD_MFR_ID = 0x99
        data, pec_ok = dev.read_block_pec(CMD_MFR_ID)
        print(f"MFR_ID: {data.decode('ascii', errors='replace')}, "
              f"PEC 校验: {'通过' if pec_ok else '失败'}")


if __name__ == '__main__':
    main()
```

> **提示**: PEC 错误的处理策略应遵循第 15 章调试与故障排查中的建议——偶发 PEC 错误应重试并保留上一次有效数据，不应立即判定为设备故障。连续多次 PEC 错误才需考虑总线信号质量或设备硬件问题。

---

## 16.5 SMBALERT 中断处理示例

SMBALERT 是 SMBus/PMBus 定义的异步通知机制。当模块检测到故障或警告条件时，拉低 SMBALERT# 引脚通知主机。SMBALERT 机制详见第 7 章，故障模型详见第 8 章。

### 16.5.1 检测 SMBALERT# 信号（GPIO 中断）

在嵌入式 Linux 系统上，SMBALERT# 信号通常连接到 GPIO 引脚，可通过 sysfs 或 libgpiod 检测。

```python
"""
smbalert_gpio.py — SMBALERT# GPIO 中断检测

演示如何在 Linux 上通过 GPIO sysfs 接口检测 SMBALERT# 信号。
适用于 Raspberry Pi、BeagleBone 等嵌入式 Linux 平台。

SMBALERT# 为低电平有效（开漏输出，需外部上拉）。
"""

import os
import time
import threading
from typing import Callable


class SMBAlertGPIO:
    """
    SMBALERT# GPIO 中断检测类。

    使用 Linux sysfs GPIO 接口检测 SMBALERT# 下降沿。
    """

    def __init__(self, gpio_pin: int):
        """
        初始化 GPIO 中断检测。

        参数:
            gpio_pin: GPIO 引脚编号（sysfs 编号，非芯片编号）
        """
        self.gpio_pin = gpio_pin
        self.gpio_path = f"/sys/class/gpio/gpio{gpio_pin}"
        self._running = False
        self._thread = None
        self._callback = None

    def _export_gpio(self) -> None:
        """导出 GPIO 引脚（如尚未导出）"""
        if not os.path.exists(self.gpio_path):
            with open('/sys/class/gpio/export', 'w') as f:
                f.write(str(self.gpio_pin))

    def _configure_gpio(self) -> None:
        """
        配置 GPIO 为输入模式，下降沿触发。

        SMBALERT# 为低电平有效信号。
        """
        # 设置方向为输入
        with open(f'{self.gpio_path}/direction', 'w') as f:
            f.write('in')

        # 设置触发方式为下降沿（falling edge）
        with open(f'{self.gpio_path}/edge', 'w') as f:
            f.write('falling')

    def setup(self) -> None:
        """初始化 GPIO"""
        self._export_gpio()
        time.sleep(0.1)  # 等待 sysfs 节点创建
        self._configure_gpio()
        print(f"GPIO {self.gpio_pin} 已配置为 SMBALERT# 输入 "
              f"(下降沿触发)")

    def read_state(self) -> bool:
        """
        读取当前 SMBALERT# 状态。

        返回:
            True = 低电平有效（有报警）, False = 高电平（无报警）
        """
        with open(f'{self.gpio_path}/value', 'r') as f:
            val = int(f.read().strip())
        # SMBALERT# 低电平有效：value=0 表示有报警
        return val == 0

    def start_monitor(self, callback: Callable[[], None]) -> None:
        """
        启动 SMBALERT# 监控线程。

        参数:
            callback: 检测到 SMBALERT# 下降沿时的回调函数
        """
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop,
                                         daemon=True)
        self._thread.start()
        print("SMBALERT# 监控线程已启动")

    def _poll_loop(self) -> None:
        """GPIO 轮询循环（使用 sysfs 中断通知）"""
        value_fd = os.open(f'{self.gpio_path}/value', os.O_RDONLY)

        # 首次读取清除 pending 状态
        os.read(value_fd, 1)
        # 使用 select 等待 sysfs 中断通知
        import select

        while self._running:
            # 等待 GPIO edge 事件（超时 1 秒，允许检查退出标志）
            readable, _, _ = select.select([value_fd], [], [], 1.0)

            if readable:
                os.lseek(value_fd, 0, os.SEEK_SET)
                val = os.read(value_fd, 1)

                # 下降沿：val = b'0'
                if val == b'0' and self._callback:
                    try:
                        self._callback()
                    except Exception as e:
                        print(f"回调函数执行出错: {e}")

        os.close(value_fd)

    def stop_monitor(self) -> None:
        """停止监控线程"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        print("SMBALERT# 监控线程已停止")


# ===== 使用示例 =====

def alert_handler():
    """SMBALERT# 中断回调函数"""
    print(f"[{time.strftime('%H:%M:%S')}] SMBALERT# 触发！检测到报警条件")


def main():
    # 配置参数
    GPIO_PIN = 17  # 示例 GPIO 引脚编号

    alert_gpio = SMBAlertGPIO(GPIO_PIN)
    alert_gpio.setup()

    # 检查当前状态
    if alert_gpio.read_state():
        print("当前 SMBALERT# 为低电平（有报警）")
    else:
        print("当前 SMBALERT# 为高电平（无报警）")

    # 启动监控
    alert_gpio.start_monitor(alert_handler)

    try:
        print("等待 SMBALERT# 事件... (Ctrl+C 退出)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        alert_gpio.stop_monitor()


if __name__ == '__main__':
    main()
```

> **提示**: 在较新的 Linux 内核上（5.x+），推荐使用 libgpiod 的字符设备接口替代 sysfs。libgpiod 提供 `gpiod` Python 包，用法类似但性能更好。上述 sysfs 方式在大多数嵌入式 Linux 发行版上仍然可用。

### 16.5.2 ARA 协议实现

当多设备共享 SMBALERT# 线时，主机需要通过 ARA（Alert Response Address）协议确定报警源设备。ARA 协议详见第 7 章。

```python
"""
smbalert_ara.py — ARA 协议实现

SMBALERT 响应地址（Alert Response Address, ARA）协议用于
多设备共享 SMBALERT# 线时，主机定位报警源设备。

ARA 地址: 0x0C (固定)
ARA 事务: 主机向 ARA 地址发送 Read Byte，报警设备以自己的从设备地址响应。

ARA 协议详见第 7 章。
"""

import smbus2
import time

# SMBus 规范定义的 Alert Response Address
ARA_ADDRESS = 0x0C


class SMBAlertHandler:
    """SMBALERT 中断处理类"""

    def __init__(self, bus: int, known_devices: list):
        """
        初始化 SMBALERT 处理器。

        参数:
            bus:           I2C 总线编号
            known_devices: 已知 PMBus 设备地址列表
                          （用于逐个轮询确认报警源）
        """
        self.bus_num = bus
        self._bus = smbus2.SMBus(bus)
        self.known_devices = known_devices

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._bus:
            self._bus.close()

    def alert_response_address(self) -> int:
        """
        执行 ARA 事务，获取报警设备的从设备地址。

        返回:
            报警设备的 7-bit 从设备地址
            如果没有设备响应，返回 0

        注意:
          - ARA 事务使用固定地址 0x0C
          - 报警设备以自己的从设备地址作为响应数据
          - 如果多个设备同时报警，最低地址的设备优先响应
          - ARA 事务会自动清除该设备的 SMBALERT# 信号
        """
        try:
            # 向 ARA 地址发送 Read Byte
            # 报警设备会 ACK 并返回自己的地址
            responding_addr = self._bus.read_byte(ARA_ADDRESS)
            return responding_addr
        except (OSError, IOError):
            # 无设备响应 ARA（可能已被清除或不存在报警源）
            return 0

    def identify_alert_source(self) -> list:
        """
        确定所有正在报警的设备地址。

        由于 ARA 协议每次只能识别一个设备（最低地址优先），
        当存在多个报警源时，需要循环执行 ARA 直到无设备响应。

        返回:
            报警设备地址列表
        """
        alert_sources = []
        max_iterations = len(self.known_devices) + 1

        for _ in range(max_iterations):
            addr = self.alert_response_address()
            if addr == 0:
                break
            alert_sources.append(addr)
            # 短暂延迟，让其他设备有机会响应
            time.sleep(0.01)

        return alert_sources

    def poll_alert_status(self, known_devices: list) -> dict:
        """
        通过轮询已知设备确认报警状态。

        在 ARA 不可用或单设备系统中，可直接读取各设备的
        STATUS_WORD 判断是否有报警。

        返回:
            {设备地址: STATUS_WORD 值} 字典
        """
        results = {}
        for addr in known_devices:
            try:
                # Read STATUS_WORD
                self._bus.write_byte(addr, 0x79)  # STATUS_WORD 命令码
                data = self._bus.read_i2c_block_data(addr, 0x79, 2)
                status_word = (data[1] << 8) | data[0]
                results[addr] = status_word
            except (OSError, IOError):
                results[addr] = None
        return results


def main():
    BUS_NUMBER = 1
    # 已知总线上的 PMBus 设备地址
    KNOWN_DEVICES = [0x58, 0x59, 0x5A]

    with SMBAlertHandler(bus=BUS_NUMBER,
                          known_devices=KNOWN_DEVICES) as handler:
        print("=== SMBALERT 报警源检测 ===")

        # 方法一：使用 ARA 协议
        sources = handler.identify_alert_source()
        if sources:
            print(f"ARA 检测到报警设备: "
                  f"{['0x{:02X}'.format(a) for a in sources]}")
        else:
            print("ARA 未检测到报警设备")

        # 方法二：轮询已知设备
        print("\n轮询设备状态:")
        status = handler.poll_alert_status(KNOWN_DEVICES)
        for addr, word in status.items():
            if word is not None and word != 0:
                print(f"  设备 0x{addr:02X}: STATUS_WORD = 0x{word:04X} "
                      f"(有报警)")
            elif word is not None:
                print(f"  设备 0x{addr:02X}: STATUS_WORD = 0x{word:04X} "
                      f"(正常)")
            else:
                print(f"  设备 0x{addr:02X}: 无响应")


if __name__ == '__main__':
    main()
```

> **提示**: 某些 PMBus 设备不支持 SMBus ARP 协议（包括 ARA）。Omnion Power 模块支持 SMBALERT 响应协议，但在多设备共享 SMBALERT# 的场景中不具备总线争用仲裁能力。因此建议在多设备系统中优先使用逐设备轮询 STATUS_WORD 的方式定位报警源。

### 16.5.3 读取并解析故障状态

检测到 SMBALERT 后，需要按状态寄存器层级逐步定位故障。状态寄存器的位域定义详见第 8 章，完整映射参见附录 D。

```python
"""
parse_fault_status.py — 故障状态解析

演示检测到 SMBALERT 后的完整故障状态读取和解析流程。
状态寄存器位域详解参见第 8 章 + 附录 D。
"""

from pmbus_base import PMBusDevice
from typing import Optional

# ===== 状态命令码 =====
CMD_STATUS_BYTE       = 0x78
CMD_STATUS_WORD       = 0x79
CMD_STATUS_VOUT       = 0x7A
CMD_STATUS_IOUT       = 0x7B
CMD_STATUS_INPUT      = 0x7C
CMD_STATUS_TEMPERATURE = 0x7D
CMD_STATUS_CML        = 0x7E

# ===== 遥测命令码 =====
CMD_READ_VOUT         = 0x8B
CMD_READ_IOUT         = 0x8C
CMD_READ_VIN          = 0x88
CMD_READ_TEMPERATURE_1 = 0x8D


def parse_status_word(status_word: int) -> list:
    """
    解析 STATUS_WORD 位域。

    STATUS_WORD 为 16-bit，包含所有类别故障的摘要。
    位域定义详见第 8 章。
    """
    alerts = []

    # 高字节：故障/警告摘要
    if status_word & 0x8000:
        alerts.append("VOUT fault")
    if status_word & 0x4000:
        alerts.append("IOUT fault/warning")
    if status_word & 0x2000:
        alerts.append("Input voltage fault")
    if status_word & 0x0800:
        alerts.append("POWER_GOOD# negated")
    if status_word & 0x0040:
        alerts.append("Unit OFF")
    if status_word & 0x0020:
        alerts.append("VOUT overvoltage")
    if status_word & 0x0010:
        alerts.append("IOUT overcurrent")
    if status_word & 0x0008:
        alerts.append("VIN undervoltage")
    if status_word & 0x0004:
        alerts.append("Temperature fault/warning")
    if status_word & 0x0002:
        alerts.append("CML fault")

    return alerts


def diagnose_vout(dev: PMBusDevice) -> list:
    """解析 STATUS_VOUT 详细故障"""
    status = dev.read_byte(CMD_STATUS_VOUT)
    faults = []
    if status & 0x80:
        faults.append("VOUT OV fault (输出过压故障)")
    if status & 0x10:
        faults.append("VOUT UV fault (输出欠压故障)")
    return faults


def diagnose_iout(dev: PMBusDevice) -> list:
    """解析 STATUS_IOUT 详细故障"""
    status = dev.read_byte(CMD_STATUS_IOUT)
    faults = []
    if status & 0x80:
        faults.append("IOUT OC fault (输出过流故障)")
    if status & 0x20:
        faults.append("IOUT OC warning (输出过流警告)")
    return faults


def diagnose_input(dev: PMBusDevice) -> list:
    """解析 STATUS_INPUT 详细故障"""
    status = dev.read_byte(CMD_STATUS_INPUT)
    faults = []
    if status & 0x80:
        faults.append("VIN OV fault (输入过压故障)")
    if status & 0x10:
        faults.append("VIN UV fault (输入欠压故障)")
    if status & 0x08:
        faults.append("Module off (low VIN, 模块因低输入电压关闭)")
    return faults


def diagnose_temperature(dev: PMBusDevice) -> list:
    """解析 STATUS_TEMPERATURE 详细故障"""
    status = dev.read_byte(CMD_STATUS_TEMPERATURE)
    faults = []
    if status & 0x80:
        faults.append("OT fault (过温故障)")
    if status & 0x40:
        faults.append("OT warning (过温警告)")
    return faults


def diagnose_cml(dev: PMBusDevice) -> list:
    """解析 STATUS_CML 通信故障"""
    status = dev.read_byte(CMD_STATUS_CML)
    faults = []
    if status & 0x80:
        faults.append("Invalid/unsupported command (无效/不支持命令)")
    if status & 0x40:
        faults.append("Invalid/unsupported data (无效/不支持数据)")
    if status & 0x20:
        faults.append("PEC fault (包错误校验失败)")
    return faults


def capture_fault_snapshot(dev: PMBusDevice) -> dict:
    """
    采集故障现场数据。

    在检测到报警后立即调用，捕获关键遥测量用于事后分析。
    """
    snapshot = {}

    try:
        snapshot['status_word'] = dev.read_word(CMD_STATUS_WORD)
    except Exception:
        snapshot['status_word'] = None

    try:
        snapshot['vout'] = dev.read_word(CMD_READ_VOUT)
    except Exception:
        snapshot['vout'] = None

    try:
        snapshot['iout'] = dev.read_word(CMD_READ_IOUT)
    except Exception:
        snapshot['iout'] = None

    try:
        snapshot['vin'] = dev.read_word(CMD_READ_VIN)
    except Exception:
        snapshot['vin'] = None

    try:
        snapshot['temperature'] = dev.read_word(CMD_READ_TEMPERATURE_1)
    except Exception:
        snapshot['temperature'] = None

    return snapshot


def handle_alert(dev: PMBusDevice) -> None:
    """
    SMBALERT 报警处理流程。

    推荐流程（参见第 8 章）:
      1. 读取 STATUS_WORD 快速判断故障类别
      2. 根据摘要位读取对应 STATUS_xxx 详细寄存器
      3. 采集关键遥测快照
      4. 记录故障现场
      5. 必要时执行 CLEAR_FAULTS
      6. 再次读取 STATUS 确认故障是否仍由实时条件触发
    """
    import time

    print("=" * 50)
    print(f"[{time.strftime('%H:%M:%S')}] SMBALERT 报警处理")
    print("=" * 50)

    # 第 1 步：读取 STATUS_WORD
    status_word = dev.read_word(CMD_STATUS_WORD)
    print(f"\nSTATUS_WORD: 0x{status_word:04X}")

    if status_word == 0:
        print("  STATUS_WORD 为零，无活跃故障")
        return

    # 解析摘要
    summary = parse_status_word(status_word)
    print(f"  摘要: {', '.join(summary) if summary else '无故障'}")

    # 第 2 步：根据摘要位深入诊断
    all_faults = []

    if status_word & (0x8000 | 0x0020):
        faults = diagnose_vout(dev)
        if faults:
            print(f"\n  STATUS_VOUT 详细:")
            for f in faults:
                print(f"    - {f}")
                all_faults.append(f)

    if status_word & (0x4000 | 0x0010):
        faults = diagnose_iout(dev)
        if faults:
            print(f"\n  STATUS_IOUT 详细:")
            for f in faults:
                print(f"    - {f}")
                all_faults.append(f)

    if status_word & (0x2000 | 0x0008):
        faults = diagnose_input(dev)
        if faults:
            print(f"\n  STATUS_INPUT 详细:")
            for f in faults:
                print(f"    - {f}")
                all_faults.append(f)

    if status_word & 0x0004:
        faults = diagnose_temperature(dev)
        if faults:
            print(f"\n  STATUS_TEMPERATURE 详细:")
            for f in faults:
                print(f"    - {f}")
                all_faults.append(f)

    if status_word & 0x0002:
        faults = diagnose_cml(dev)
        if faults:
            print(f"\n  STATUS_CML 详细:")
            for f in faults:
                print(f"    - {f}")
                all_faults.append(f)

    # 第 3 步：采集故障现场
    print(f"\n  故障现场快照:")
    snapshot = capture_fault_snapshot(dev)
    for k, v in snapshot.items():
        if v is not None:
            print(f"    {k}: 0x{v:04X}" if isinstance(v, int) else f"    {k}: {v}")

    # 第 4 步：根据故障类型决定后续操作
    # 注意：CLEAR_FAULTS 只清除 latch 状态，不修复根本原因
    # 详见第 8 章
    has_latched_fault = bool(status_word & 0xFFFF)
    if has_latched_fault and not (status_word & 0x0002):
        # 如果不是纯通信故障，可以选择清除 latch 后检查是否复现
        print(f"\n  建议: 如果故障条件已消除，可执行 CLEAR_FAULTS 后观察")


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        # 读取并显示当前状态
        status_word = dev.read_word(CMD_STATUS_WORD)
        print(f"当前 STATUS_WORD: 0x{status_word:04X}")

        if status_word != 0:
            handle_alert(dev)
        else:
            print("当前无活跃故障")

            # 模拟：演示完整报警处理流程
            print("\n--- 模拟报警处理 ---")
            print("(假设 STATUS_WORD 不为零)")
            print("实际使用时，handle_alert() 应在 SMBALERT# 中断回调中调用")


if __name__ == '__main__':
    main()
```

---

## 16.6 故障管理示例

### 16.6.1 设置保护阈值

保护阈值的设置需要遵循交叉检查规则，避免配置冲突。阈值设置详见第 8 章，各命令的默认值和可编程范围参见具体产品 Datasheet。

```python
"""
set_protection_limits.py — 设置保护阈值

演示如何正确设置 PMBus 保护阈值，包括交叉检查和写保护处理。
保护功能详解参见第 8 章。
"""

from pmbus_base import PMBusDevice

# ===== 命令码 =====
CMD_WRITE_PROTECT        = 0x10
CMD_MFR_DEVICE_TYPE      = 0xD0  # 写保护控制
CMD_VOUT_COMMAND         = 0x21
CMD_VOUT_OV_FAULT_LIMIT  = 0x40
CMD_IOUT_OC_FAULT_LIMIT  = 0x46
CMD_IOUT_OC_WARN_LIMIT   = 0x4A
CMD_OT_FAULT_LIMIT       = 0x4F
CMD_OT_WARN_LIMIT        = 0x51


def disable_write_protect(dev: PMBusDevice) -> None:
    """
    临时关闭写保护。

    写保护由 MFR_DEVICE_TYPE (0xD0) 的 bit 1 (WPE) 控制。
    关闭写保护不会影响 NVM 中保存的设置，下次上电或 RESTORE 后恢复。
    写保护机制详见第 9 章。
    """
    current = dev.read_word(CMD_MFR_DEVICE_TYPE)
    new_val = current & ~0x0002  # 清除 WPE 位
    dev.write_word(CMD_MFR_DEVICE_TYPE, new_val)
    print(f"写保护已关闭 (MFR_DEVICE_TYPE: "
          f"0x{current:04X} → 0x{new_val:04X})")


def enable_write_protect(dev: PMBusDevice) -> None:
    """重新启用写保护"""
    current = dev.read_word(CMD_MFR_DEVICE_TYPE)
    new_val = current | 0x0002  # 置位 WPE 位
    dev.write_word(CMD_MFR_DEVICE_TYPE, new_val)
    print(f"写保护已启用 (MFR_DEVICE_TYPE: "
          f"0x{current:04X} → 0x{new_val:04X})")


def set_ovp_limit(dev: PMBusDevice, voltage: float,
                  vout_exp: int) -> None:
    """
    设置输出过压保护（OVP）阈值。

    交叉检查: VOUT_OV_FAULT_LIMIT 必须 > VOUT_COMMAND。
    自动覆盖: 最大 OV 限制 = VOUT_COMMAND + 2V（由模块强制执行）。

    参数:
        voltage:  目标 OVP 阈值（V）
        vout_exp: VOUT_MODE 指数
    """
    # 读取当前 VOUT_COMMAND
    vout_raw = dev.read_word(CMD_VOUT_COMMAND)
    vout_current = vout_raw * (2.0 ** vout_exp)

    # 交叉检查
    if voltage <= vout_current:
        raise ValueError(
            f"OVP 阈值 ({voltage} V) 必须大于当前 VOUT_COMMAND "
            f"({vout_current:.3f} V)"
        )

    # 检查自动覆盖上限
    max_ovp = vout_current + 2.0
    if voltage > max_ovp:
        print(f"警告: OVP 阈值 {voltage} V 超过自动覆盖上限 "
              f"{max_ovp:.1f} V，模块将自动限制为 {max_ovp:.1f} V")
        voltage = min(voltage, 15.99)  # 最大值限制

    # 编码并写入
    mantissa = round(voltage / (2.0 ** vout_exp))
    dev.write_word(CMD_VOUT_OV_FAULT_LIMIT, mantissa)
    print(f"VOUT_OV_FAULT_LIMIT: {voltage:.3f} V "
          f"(数据字: 0x{mantissa:04X})")


def set_ocp_limits(dev: PMBusDevice,
                   fault_limit: float, warn_limit: float) -> None:
    """
    设置输出过流保护（OCP）阈值。

    交叉检查: IOUT_OC_FAULT_LIMIT 必须 > IOUT_OC_WARN_LIMIT。

    参数:
        fault_limit: 过流故障阈值（A）
        warn_limit:  过流警告阈值（A）
    """
    if fault_limit <= warn_limit:
        raise ValueError(
            f"OCP 故障阈值 ({fault_limit} A) 必须大于 "
            f"警告阈值 ({warn_limit} A)"
        )

    # 注意：IOUT 相关命令使用 Linear11 格式
    # 此处需要编码函数（简化示例，实际应根据命令的固定指数编码）
    from telemetry_decode import linear11_encode

    fault_word = linear11_encode(fault_limit)
    warn_word = linear11_encode(warn_limit)

    # 先设置警告阈值（较小值），再设置故障阈值（较大值）
    # 避免中间状态违反交叉检查规则
    dev.write_word(CMD_IOUT_OC_WARN_LIMIT, warn_word)
    print(f"IOUT_OC_WARN_LIMIT: {warn_limit:.1f} A")

    dev.write_word(CMD_IOUT_OC_FAULT_LIMIT, fault_word)
    print(f"IOUT_OC_FAULT_LIMIT: {fault_limit:.1f} A")


def set_otp_limits(dev: PMBusDevice,
                   fault_limit: float, warn_limit: float) -> None:
    """
    设置过温保护（OTP）阈值。

    交叉检查: OT_FAULT_LIMIT 必须 > OT_WARN_LIMIT。
    """
    if fault_limit <= warn_limit:
        raise ValueError(
            f"OTP 故障阈值 ({fault_limit} °C) 必须大于 "
            f"警告阈值 ({warn_limit} °C)"
        )

    from telemetry_decode import linear11_encode

    fault_word = linear11_encode(fault_limit)
    warn_word = linear11_encode(warn_limit)

    dev.write_word(CMD_OT_WARN_LIMIT, warn_word)
    print(f"OT_WARN_LIMIT: {warn_limit:.1f} °C")

    dev.write_word(CMD_OT_FAULT_LIMIT, fault_word)
    print(f"OT_FAULT_LIMIT: {fault_limit:.1f} °C")


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        # 读取 VOUT_MODE
        vout_mode_raw = dev.read_byte(0x20)
        vout_exp = -(vout_mode_raw & 0x0F)

        print("=== 设置保护阈值 ===\n")

        # 1. 关闭写保护
        disable_write_protect(dev)
        print()

        try:
            # 2. 设置 OVP
            set_ovp_limit(dev, 14.0, vout_exp)
            print()

            # 3. 设置 OCP（需要 linear11_encode，此处为示例）
            # set_ocp_limits(dev, fault_limit=210.0, warn_limit=200.0)
            # print()

            # 4. 设置 OTP（需要 linear11_encode，此处为示例）
            # set_otp_limits(dev, fault_limit=125.0, warn_limit=116.0)
            # print()

        finally:
            # 5. 重新启用写保护
            enable_write_protect(dev)

        print("\n提示: 修改阈值后如需持久化，执行 STORE_DEFAULT_ALL (0x11)")
        print("注意: 不当的阈值设置可能导致模块或系统损坏")


if __name__ == '__main__':
    main()
```

> **提示**: 保护阈值的具体范围和默认值因产品型号而异，设置前应参考具体产品 Datasheet。生产环境中修改保护阈值前，建议联系 Omnion Power FAE 确认。

### 16.6.2 故障监控循环

以下示例实现一个完整的故障监控循环，结合轮询和 SMBALERT 中断，遵循第 14 章中描述的主机驱动状态机。

```python
"""
fault_monitor.py — 故障监控循环

实现基于轮询 + SMBALERT 中断的故障监控系统。
遵循第 14 章描述的主机驱动状态机设计。

状态:
  NORMAL_POLL     — 正常轮询遥测和状态
  ALERT_HANDLING  — SMBALERT 触发，深入诊断
  FAULT_RECOVERY  — 故障恢复处理
"""

import time
import threading
from enum import Enum
from pmbus_base import PMBusDevice
from parse_fault_status import handle_alert, parse_status_word


class MonitorState(Enum):
    """监控状态"""
    NORMAL_POLL = "normal_poll"
    ALERT_HANDLING = "alert_handling"
    FAULT_RECOVERY = "fault_recovery"


class FaultMonitor:
    """
    PMBus 故障监控器。

    功能:
      - 周期性轮询 STATUS_WORD
      - 检测到异常时深入诊断
      - 记录故障历史
      - 支持外部 SMBALERT 中断触发
    """

    def __init__(self, dev: PMBusDevice,
                 poll_interval: float = 1.0,
                 max_consecutive_errors: int = 5):
        """
        参数:
            dev:                   PMBus 设备实例
            poll_interval:         正常轮询间隔（秒）
            max_consecutive_errors: 连续通信错误上限（超过则降级）
        """
        self.dev = dev
        self.poll_interval = poll_interval
        self.max_errors = max_consecutive_errors
        self.state = MonitorState.NORMAL_POLL
        self._running = False
        self._thread = None
        self._consecutive_errors = 0
        self._alert_event = threading.Event()
        self.fault_history = []

    def start(self) -> None:
        """启动监控循环"""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop,
                                         daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止监控循环"""
        self._running = False
        self._alert_event.set()  # 唤醒可能阻塞的线程
        if self._thread:
            self._thread.join(timeout=3.0)

    def trigger_alert(self) -> None:
        """
        外部 SMBALERT# 中断触发。

        由 GPIO 监控线程在检测到 SMBALERT# 下降沿时调用。
        """
        self._alert_event.set()

    def _read_status_word_safe(self) -> int:
        """安全读取 STATUS_WORD，带错误计数"""
        try:
            status = self.dev.read_word(0x79)
            self._consecutive_errors = 0
            return status
        except Exception as e:
            self._consecutive_errors += 1
            print(f"读取 STATUS_WORD 失败 (连续第 "
                  f"{self._consecutive_errors} 次): {e}")
            return -1

    def _normal_poll(self) -> None:
        """正常轮询流程"""
        status_word = self._read_status_word_safe()

        if status_word < 0:
            # 通信错误
            if self._consecutive_errors >= self.max_errors:
                print(f"连续 {self.max_errors} 次通信错误，"
                      f"进入 FAULT_RECOVERY 状态")
                self.state = MonitorState.FAULT_RECOVERY
            return

        if status_word != 0:
            # 检测到故障/警告，进入报警处理
            print(f"STATUS_WORD = 0x{status_word:04X}, "
                  f"检测到异常，进入 ALERT_HANDLING")
            self.state = MonitorState.ALERT_HANDLING
            return

        # 正常状态，可在此处读取遥测数据
        # （示例中省略遥测读取，实际应用中根据需要添加）

    def _alert_handling(self) -> None:
        """报警处理流程"""
        try:
            handle_alert(self.dev)
            self.fault_history.append({
                'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': str(self.state),
            })

            # 检查处理后状态
            status_word = self.dev.read_word(0x79)
            if status_word == 0:
                print("故障已清除，恢复正常轮询")
                self.state = MonitorState.NORMAL_POLL
            else:
                print(f"故障仍存在 (STATUS_WORD=0x{status_word:04X})")
        except Exception as e:
            print(f"报警处理出错: {e}")
        finally:
            # 返回正常轮询
            self.state = MonitorState.NORMAL_POLL

    def _fault_recovery(self) -> None:
        """
        故障恢复流程。

        策略（参见第 14 章）:
          - 短暂延迟后重试通信
          - 如果恢复成功，返回正常轮询
          - 如果持续失败，标记设备为 degraded
        """
        print(f"故障恢复中... (连续错误: "
              f"{self._consecutive_errors})")
        time.sleep(2.0)

        status = self._read_status_word_safe()
        if status >= 0:
            print("通信已恢复")
            self.state = MonitorState.NORMAL_POLL
        else:
            print(f"通信仍未恢复，继续等待...")

    def _monitor_loop(self) -> None:
        """主监控循环"""
        print(f"故障监控已启动 (轮询间隔: {self.poll_interval}s)")

        while self._running:
            # 检查是否有外部 SMBALERT 触发
            if self._alert_event.is_set():
                self._alert_event.clear()
                self.state = MonitorState.ALERT_HANDLING

            # 根据状态执行对应流程
            if self.state == MonitorState.NORMAL_POLL:
                self._normal_poll()
            elif self.state == MonitorState.ALERT_HANDLING:
                self._alert_handling()
            elif self.state == MonitorState.FAULT_RECOVERY:
                self._fault_recovery()

            # 等待下一次轮询（可被 SMBALERT 中断唤醒）
            self._alert_event.wait(timeout=self.poll_interval)


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        monitor = FaultMonitor(dev, poll_interval=1.0)
        monitor.start()

        try:
            print("监控运行中... (Ctrl+C 退出)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止监控...")
            monitor.stop()
            print(f"故障历史记录: {len(monitor.fault_history)} 条")


if __name__ == '__main__':
    main()
```

### 16.6.3 CLEAR_FAULTS 操作

`CLEAR_FAULTS` 命令用于清除已锁存的故障状态和 SMBALERT# 信号。该命令不会修复故障的根本原因——如果导致故障的物理条件仍然存在，相关状态位可能在清除后立即重新置位。CLEAR_FAULTS 行为详见第 8 章。

```python
"""
clear_faults.py — CLEAR_FAULTS 操作

演示 CLEAR_FAULTS 命令的正确使用方式。
"""

import time
from pmbus_base import PMBusDevice

CMD_CLEAR_FAULTS = 0x03
CMD_STATUS_WORD   = 0x79
CMD_STATUS_VOUT   = 0x7A
CMD_STATUS_IOUT   = 0x7B
CMD_STATUS_CML    = 0x7E


def clear_faults(dev: PMBusDevice) -> bool:
    """
    执行 CLEAR_FAULTS 命令。

    CLEAR_FAULTS 会清除:
      - 所有 STATUS_xxx 寄存器中的 latch 状态
      - 活动的 SMBALERT# 信号

    返回:
        True 表示命令执行成功
    """
    try:
        dev.send_byte(CMD_CLEAR_FAULTS)
        return True
    except Exception as e:
        print(f"CLEAR_FAULTS 执行失败: {e}")
        return False


def verify_faults_cleared(dev: PMBusDevice) -> dict:
    """
    验证故障是否已清除。

    读取 STATUS_WORD 确认是否仍有活跃故障。
    如果有，可能是实时条件仍在触发。

    返回:
        {'cleared': bool, 'status_word': int}
    """
    # 短暂延迟，确保命令已处理
    time.sleep(0.05)

    try:
        status_word = dev.read_word(CMD_STATUS_WORD)
        return {
            'cleared': status_word == 0,
            'status_word': status_word,
        }
    except Exception:
        return {'cleared': False, 'status_word': None}


def safe_clear_faults(dev: PMBusDevice) -> dict:
    """
    安全的故障清除流程。

    步骤:
      1. 记录清除前的故障状态
      2. 执行 CLEAR_FAULTS
      3. 等待设备处理
      4. 验证故障是否仍存在（判断是 latch 还是实时条件）
      5. 如果故障复现，记录实时条件

    返回:
        包含清除前后状态和验证结果的字典
    """
    result = {}

    # 步骤 1: 记录清除前状态
    result['before'] = {
        'status_word': dev.read_word(CMD_STATUS_WORD),
    }

    print(f"清除前 STATUS_WORD: "
          f"0x{result['before']['status_word']:04X}")

    # 步骤 2: 执行清除
    success = clear_faults(dev)
    result['clear_success'] = success

    if not success:
        return result

    print("CLEAR_FAULTS 已执行")

    # 步骤 3-4: 验证
    time.sleep(0.1)
    verification = verify_faults_cleared(dev)
    result['after'] = verification

    if verification['cleared']:
        print("验证: 故障已清除（latch 状态）")
    else:
        print(f"验证: 故障仍存在 "
              f"(STATUS_WORD=0x{verification['status_word']:04X})")
        print("  → 可能是实时条件仍在触发，"
              "需排查根本原因")

    return result


def main():
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58

    with PMBusDevice(bus=BUS_NUMBER, addr=DEVICE_ADDR) as dev:
        print("=== CLEAR_FAULTS 操作演示 ===\n")

        # 清除前先检查状态
        status = dev.read_word(CMD_STATUS_WORD)
        if status == 0:
            print("当前无活跃故障，无需清除")
        else:
            result = safe_clear_faults(dev)

            # 如果故障复现，读取详细状态
            if not result['after']['cleared']:
                print("\n故障复现，读取详细状态寄存器:")
                try:
                    vout = dev.read_byte(CMD_STATUS_VOUT)
                    iout = dev.read_byte(CMD_STATUS_IOUT)
                    cml = dev.read_byte(CMD_STATUS_CML)
                    print(f"  STATUS_VOUT: 0x{vout:02X}")
                    print(f"  STATUS_IOUT: 0x{iout:02X}")
                    print(f"  STATUS_CML:  0x{cml:02X}")
                except Exception as e:
                    print(f"  读取详细状态失败: {e}")
```

---

## 16.7 完整的初始化序列示例

以下代码展示从上电到正常运行的完整初始化序列，整合了前面各节的功能。初始化序列遵循第 13 章描述的上电与启动行为，以及第 14 章的主机驱动状态机设计。

```python
"""
pmbus_init_sequence.py — 完整的 PMBus 初始化序列

从上电到正常运行的完整流程，包括：
  1. 总线扫描与设备发现
  2. 设备信息确认
  3. 写保护管理
  4. 配置参数设置
  5. ON/OFF 行为配置
  6. 保护阈值设置
  7. 输出开启与验证
  8. 故障监控启动

Bring-up Checklist 详见第 14 章。
"""

import time
from typing import Optional
from pmbus_base import PMBusDevice

# ===== 命令码汇总 =====
# 系统控制
CMD_OPERATION         = 0x01
CMD_ON_OFF_CONFIG     = 0x02
CMD_CLEAR_FAULTS      = 0x03
CMD_WRITE_PROTECT     = 0x10
CMD_STORE_DEFAULT_ALL = 0x11
CMD_RESTORE_DEFAULT_ALL = 0x12
CMD_CAPABILITY        = 0x19
CMD_PMBUS_REVISION    = 0x98

# 输出电压
CMD_VOUT_MODE         = 0x20
CMD_VOUT_COMMAND      = 0x21
CMD_VOUT_MARGIN_HIGH  = 0x25
CMD_VOUT_MARGIN_LOW   = 0x26

# 保护阈值
CMD_VOUT_OV_FAULT_LIMIT = 0x40
CMD_IOUT_OC_FAULT_LIMIT = 0x46

# 制造商
CMD_MFR_ID            = 0x99
CMD_MFR_MODEL         = 0x9A
CMD_MFR_FW_REV        = 0xDB
CMD_MFR_DEVICE_TYPE   = 0xD0

# 状态
CMD_STATUS_WORD       = 0x79
CMD_STATUS_CML        = 0x7E

# 遥测
CMD_READ_VOUT         = 0x8B
CMD_READ_VIN          = 0x88


class PMBusInitError(Exception):
    """PMBus 初始化异常"""
    pass


class PMBusInitializer:
    """PMBus 完整初始化序列"""

    def __init__(self, bus: int, addr: int,
                 expected_mfr_id: str = "OMPW"):
        self.bus = bus
        self.addr = addr
        self.expected_mfr_id = expected_mfr_id
        self.dev: Optional[PMBusDevice] = None
        self.vout_exp = -12  # 默认值，初始化时从设备读取

    # ===== 步骤 1: 设备发现 =====

    def scan_bus(self, bus: int) -> list:
        """
        扫描 I2C 总线上的设备。

        通过尝试通信每个可能的 7-bit 地址来发现设备。
        """
        found = []
        test_dev = PMBusDevice(bus=bus, addr=0, pec=False)

        print(f"扫描 I2C 总线 {bus}...")
        for addr in range(0x08, 0x78):  # 有效 7-bit 地址范围
            test_dev.addr = addr
            try:
                # 尝试读取 PMBUS_REVISION 作为探测命令
                test_dev.read_byte(CMD_PMBUS_REVISION)
                found.append(addr)
                print(f"  发现设备: 0x{addr:02X}")
            except Exception:
                pass

        test_dev.close()
        return found

    # ===== 步骤 2: 设备信息确认 =====

    def verify_device(self) -> None:
        """确认设备身份和协议版本"""
        print("\n--- 步骤 2: 设备信息确认 ---")

        # 读取 PMBUS_REVISION
        revision = self.dev.read_byte(CMD_PMBUS_REVISION)
        part1 = (revision >> 5) & 0x07
        part2 = revision & 0x0F
        print(f"PMBus 协议版本: Part I = {part1}, Part II = {part2}")

        # 读取 CAPABILITY
        cap = self.dev.read_byte(CMD_CAPABILITY)
        pec_support = bool(cap & 0x20)
        print(f"PEC 支持: {'是' if pec_support else '否'}")

        # 读取 MFR_ID
        mfr_id = self.dev.read_block(CMD_MFR_ID).decode('ascii').strip()
        print(f"制造商 ID: {mfr_id}")

        if self.expected_mfr_id and mfr_id != self.expected_mfr_id:
            raise PMBusInitError(
                f"制造商 ID 不匹配: 期望 '{self.expected_mfr_id}', "
                f"实际 '{mfr_id}'"
            )

        # 读取 MFR_MODEL
        mfr_model = self.dev.read_block(CMD_MFR_MODEL).decode('ascii').strip()
        print(f"产品型号: {mfr_model}")

        # 读取固件版本
        fw_raw = self.dev.read_word(CMD_MFR_FW_REV)
        fw_ver = (f"{(fw_raw >> 12) & 0x0F}."
                  f"{(fw_raw >> 8) & 0x0F}."
                  f"{(fw_raw >> 4) & 0x0F}{fw_raw & 0x0F}")
        print(f"固件版本: {fw_ver}")

    # ===== 步骤 3: 清除旧故障 =====

    def clear_existing_faults(self) -> None:
        """清除可能残留的历史故障"""
        print("\n--- 步骤 3: 清除历史故障 ---")

        status = self.dev.read_word(CMD_STATUS_WORD)
        if status != 0:
            print(f"检测到残留故障: STATUS_WORD = 0x{status:04X}")

            # 检查 CML 错误
            cml = self.dev.read_byte(CMD_STATUS_CML)
            if cml & 0x20:
                print("  注意: 检测到 PEC 错误记录，检查总线信号质量")

            self.dev.send_byte(CMD_CLEAR_FAULTS)
            print("CLEAR_FAULTS 已执行")

            # 验证
            time.sleep(0.05)
            status = self.dev.read_word(CMD_STATUS_WORD)
            if status != 0:
                print(f"警告: 故障仍存在 STATUS_WORD = 0x{status:04X}")
            else:
                print("故障已清除")
        else:
            print("无残留故障")

    # ===== 步骤 4: 读取 VOUT_MODE =====

    def read_vout_mode(self) -> None:
        """读取 VOUT_MODE 获取电压编码指数"""
        print("\n--- 步骤 4: 读取 VOUT_MODE ---")

        raw = self.dev.read_byte(CMD_VOUT_MODE)
        mode = (raw >> 5) & 0x07
        n = raw & 0x0F
        self.vout_exp = -n

        print(f"VOUT_MODE: 0x{raw:02X}")
        print(f"  模式: {'Linear' if mode == 0 else f'Unknown({mode})'}")
        print(f"  指数: {self.vout_exp}")

    # ===== 步骤 5: 配置 ON/OFF 行为 =====

    def configure_on_off(self) -> None:
        """
        配置 ON/OFF 行为，确保模块响应总线控制。

        ON_OFF_CONFIG 详见第 9 章。
        """
        print("\n--- 步骤 5: 配置 ON/OFF 行为 ---")

        config = self.dev.read_byte(CMD_ON_OFF_CONFIG)
        print(f"当前 ON_OFF_CONFIG: 0x{config:02X}")

        # 确保 OPERATION 位（bit 3）被置位
        if not (config & 0x08):
            new_config = config | 0x08
            self.dev.write_byte(CMD_ON_OFF_CONFIG, new_config)
            print(f"已启用 OPERATION 总线控制: "
                  f"0x{config:02X} → 0x{new_config:02X}")
        else:
            print("OPERATION 总线控制已启用")

    # ===== 步骤 6: 设置输出电压 =====

    def set_output_voltage(self, voltage: float) -> None:
        """
        设置输出电压。

        参数:
            voltage: 目标电压（V）
        """
        print(f"\n--- 步骤 6: 设置输出电压 ---")

        # 关闭写保护
        self._disable_write_protect()

        try:
            # 编码并写入
            mantissa = round(voltage / (2.0 ** self.vout_exp))

            if mantissa < 0 or mantissa > 0xFFFF:
                raise PMBusInitError(
                    f"电压 {voltage} V 超出可编码范围"
                )

            self.dev.write_word(CMD_VOUT_COMMAND, mantissa)
            print(f"VOUT_COMMAND: {voltage:.3f} V (0x{mantissa:04X})")

            # 回读验证
            readback = self.dev.read_word(CMD_VOUT_COMMAND)
            readback_v = readback * (2.0 ** self.vout_exp)
            print(f"回读验证: {readback_v:.3f} V")

            if readback != mantissa:
                print(f"警告: 回读值不匹配 "
                      f"(写入 0x{mantissa:04X}, 回读 0x{readback:04X})")

        finally:
            self._enable_write_protect()

    # ===== 步骤 7: 开启输出 =====

    def turn_on_output(self) -> None:
        """开启模块输出"""
        print("\n--- 步骤 7: 开启输出 ---")

        current = self.dev.read_byte(CMD_OPERATION)
        new_val = current | 0x80  # 置位 ON/OFF
        self.dev.write_byte(CMD_OPERATION, new_val)
        print(f"OUTPUT ON (OPERATION: 0x{current:02X} → 0x{new_val:02X})")

    # ===== 步骤 8: 验证运行状态 =====

    def verify_operation(self) -> None:
        """验证模块正常运行"""
        print("\n--- 步骤 8: 验证运行状态 ---")

        # 等待输出建立
        time.sleep(0.5)

        # 检查状态
        status = self.dev.read_word(CMD_STATUS_WORD)
        off_flag = bool(status & 0x0040)

        if off_flag:
            raise PMBusInitError("模块处于 OFF 状态，请检查输入电源")

        # 读取遥测
        vout_raw = self.dev.read_word(CMD_READ_VOUT)
        vout = vout_raw * (2.0 ** self.vout_exp)

        vin_raw = self.dev.read_word(CMD_READ_VIN)
        # VIN 使用 Linear11 格式
        exp = ((vin_raw >> 11) & 0x1F)
        if exp & 0x10:
            exp -= 32
        mantissa = vin_raw & 0x7FF
        if mantissa & 0x400:
            mantissa -= 2048
        vin = mantissa * (2.0 ** exp)

        print(f"输出电压: {vout:.3f} V")
        print(f"输入电压: {vin:.3f} V")
        print(f"STATUS_WORD: 0x{status:04X}")

        # 检查输出电压合理性
        vout_cmd = self.dev.read_word(CMD_VOUT_COMMAND)
        vout_cmd_v = vout_cmd * (2.0 ** self.vout_exp)

        if abs(vout - vout_cmd_v) / vout_cmd_v > 0.05:
            print(f"警告: 实际输出电压 {vout:.3f} V 与设定值 "
                  f"{vout_cmd_v:.3f} V 偏差超过 5%")
        else:
            print(f"输出电压正常 (偏差: "
                  f"{abs(vout - vout_cmd_v) * 1000:.1f} mV)")

    # ===== 辅助方法 =====

    def _disable_write_protect(self) -> None:
        """关闭写保护"""
        current = self.dev.read_word(CMD_MFR_DEVICE_TYPE)
        if current & 0x0002:
            self.dev.write_word(CMD_MFR_DEVICE_TYPE,
                                current & ~0x0002)

    def _enable_write_protect(self) -> None:
        """启用写保护"""
        current = self.dev.read_word(CMD_MFR_DEVICE_TYPE)
        if not (current & 0x0002):
            self.dev.write_word(CMD_MFR_DEVICE_TYPE,
                                current | 0x0002)

    # ===== 主初始化流程 =====

    def initialize(self, target_voltage: float = None) -> bool:
        """
        执行完整的初始化序列。

        参数:
            target_voltage: 目标输出电压（V），None 则保持默认值

        返回:
            True 表示初始化成功
        """
        print("=" * 55)
        print("  PMBus 初始化序列")
        print("=" * 55)
        print(f"总线: {self.bus}, 地址: 0x{self.addr:02X}")
        print(f"目标电压: {target_voltage if target_voltage else '保持默认'}")
        print()

        try:
            self.dev = PMBusDevice(bus=self.bus, addr=self.addr)

            # 步骤 1-2: 设备发现与确认
            self.verify_device()

            # 步骤 3: 清除旧故障
            self.clear_existing_faults()

            # 步骤 4: 读取 VOUT_MODE
            self.read_vout_mode()

            # 步骤 5: 配置 ON/OFF
            self.configure_on_off()

            # 步骤 6: 设置输出电压（可选）
            if target_voltage is not None:
                self.set_output_voltage(target_voltage)

            # 步骤 7: 开启输出
            self.turn_on_output()

            # 步骤 8: 验证
            self.verify_operation()

            print("\n" + "=" * 55)
            print("  初始化完成 — 模块正常运行")
            print("=" * 55)
            return True

        except PMBusInitError as e:
            print(f"\n初始化失败: {e}")
            return False
        except Exception as e:
            print(f"\n初始化异常: {e}")
            return False
        finally:
            if self.dev:
                self.dev.close()
                self.dev = None


def main():
    """
    完整初始化示例。

    在实际应用中，以下参数应根据系统配置调整：
      - BUS_NUMBER: I2C 总线编号
      - DEVICE_ADDR: PMBus 设备地址
      - TARGET_VOLTAGE: 目标输出电压（None 表示保持默认）
    """
    # ===== 配置参数 =====
    BUS_NUMBER = 1
    DEVICE_ADDR = 0x58  # 需根据实际地址配置修改
    TARGET_VOLTAGE = None  # None = 保持出厂默认值，如 12.0V

    initializer = PMBusInitializer(
        bus=BUS_NUMBER,
        addr=DEVICE_ADDR,
        expected_mfr_id="OMPW"
    )

    success = initializer.initialize(target_voltage=TARGET_VOLTAGE)

    if success:
        # 初始化成功后，可启动故障监控（参见 16.6.2）
        print("\n提示: 可启动故障监控循环持续监测设备状态")
    else:
        print("\n提示: 请检查硬件连接和配置后重试")
        print("  - 确认 I2C 总线编号和设备地址正确")
        print("  - 确认 USB-to-I2C 适配器已连接")
        print("  - 确认输入电源已上电")
        print("  - 使用 i2cdetect -y <bus> 扫描设备")


if __name__ == '__main__':
    main()
```

> **提示**: 上述初始化序列覆盖了 Bring-up Checklist（参见第 14 章）中的关键步骤。在生产环境中，建议将配置参数外部化（如 JSON/YAML 配置文件），并增加更详细的日志记录和超时处理。

---

## 附录：完整命令码速查表

以下是本章代码中使用的 PMBus 命令码汇总，完整命令列表参见附录 A。

| 命令 | 命令码 | 传输类型 | 说明 |
|------|--------|----------|------|
| OPERATION | 0x01 | R/W Byte | 输出开关与裕量控制 |
| ON_OFF_CONFIG | 0x02 | Read Byte | ON/OFF 行为配置 |
| CLEAR_FAULTS | 0x03 | Send Byte | 清除故障状态 |
| WRITE_PROTECT | 0x10 | R/W Byte | 写保护控制 |
| STORE_DEFAULT_ALL | 0x11 | Send Byte | 存储到 NVM |
| RESTORE_DEFAULT_ALL | 0x12 | Send Byte | 恢复 NVM 配置 |
| CAPABILITY | 0x19 | Read Byte | 能力寄存器 |
| VOUT_MODE | 0x20 | Read Byte | VOUT 指数 |
| VOUT_COMMAND | 0x21 | R/W Word | 输出电压设定值 |
| VOUT_MARGIN_HIGH | 0x25 | R/W Word | 高裕量电压 |
| VOUT_MARGIN_LOW | 0x26 | R/W Word | 低裕量电压 |
| VOUT_OV_FAULT_LIMIT | 0x40 | R/W Word | 过压保护阈值 |
| IOUT_OC_FAULT_LIMIT | 0x46 | R/W Word | 过流保护阈值 |
| IOUT_OC_WARN_LIMIT | 0x4A | R/W Word | 过流警告阈值 |
| OT_FAULT_LIMIT | 0x4F | R/W Word | 过温保护阈值 |
| OT_WARN_LIMIT | 0x51 | R/W Word | 过温警告阈值 |
| STATUS_WORD | 0x79 | Read Word | 状态摘要 |
| STATUS_VOUT | 0x7A | Read Byte | 输出电压状态 |
| STATUS_IOUT | 0x7B | Read Byte | 输出电流状态 |
| STATUS_INPUT | 0x7C | Read Byte | 输入电压状态 |
| STATUS_TEMPERATURE | 0x7D | Read Byte | 温度状态 |
| STATUS_CML | 0x7E | Read Byte | 通信/存储器状态 |
| READ_VIN | 0x88 | Read Word | 读取输入电压 |
| READ_VOUT | 0x8B | Read Word | 读取输出电压 |
| READ_IOUT | 0x8C | Read Word | 读取输出电流 |
| READ_TEMPERATURE_1 | 0x8D | Read Word | 读取温度 |
| PMBUS_REVISION | 0x98 | Read Byte | PMBus 协议版本 |
| MFR_ID | 0x99 | Block Read | 制造商 ID |
| MFR_MODEL | 0x9A | Block Read | 产品型号 |
| MFR_REVISION | 0x9B | Block Read | 硬件修订版本 |
| MFR_DATE | 0x9D | Block Read | 制造日期 |
| MFR_SERIAL | 0x9E | Block Read | 序列号 |
| MFR_DEVICE_TYPE | 0xD0 | R/W Word | 写保护与模块配置 |
| MFR_FW_REV | 0xDB | Read Word | 固件版本 |
