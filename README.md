# 小米 BE7000 OpenWrt

面向小米 BE7000（Qualcomm IPQ9554 / Cortex-A73）的专用 OpenWrt 固件源码仓库，基于 [coolsnowwolf/lede](https://github.com/coolsnowwolf/lede) 构建，导入基线提交为 [`bc7f99dd`](https://github.com/coolsnowwolf/lede/commit/bc7f99dd449ac05543d8bbbd42b21ddb33c70cae)。仓库仅保留 `qualcommbe/ipq95xx` 下的 `xiaomi_be7000` 目标及其构建依赖。

## 功能

- **单一机型与架构优化**：移除无关平台与其他开发板定义，针对 IPQ9554 四核 Cortex-A73（`-mcpu=cortex-a73`）与 Linux 6.18 构建 `factory.ubi` 和 `sysupgrade.bin` 镜像。
- **开源网络与无线驱动栈**：采用 `kmod-qcom-ppe` 有线/PPE 卸载、`kmod-ath11k-ahb`（2.4G IPQ9574）与 `kmod-ath12k`（5G PCIe QCN9274），并在 `ipq-wifi-xiaomi_be7000` 中封装两颗射频的专属 `board-2.bin`。
- **原厂 ART 布局与空槽 MAC 回退**：按小米 BE7000 原厂 `0:art` 分区映射 `wan`（`0x0`）、`lan1`（`0x6`）、`lan2`（`0xc`）、`lan3`（`0x12`）以及 2.4G（`0x100e`、`0x1000`/`0x20000`）和 5G（`0x65010`、`0x65000`/`0x2d000`）。当原厂第四个有线槽位（`0x12`）为全 `FF` 或发生地址冲突时，由 [`be7000-mac.sh`](target/linux/qualcommbe/ipq95xx/base-files/lib/functions/be7000-mac.sh) 确定性派生本地管理单播 MAC。
- **纯净精简默认配置**：仅包含 Bootstrap 主题中文 LuCI、FW4/nftables、PPPoE、IPv6、Dropbear SSH 与 `zram-swap`，不包含代理、VPN、容器、NAS、FTP、UPnP 或 KMS 等无关插件。

## 快速开始

从 [GitHub Releases](https://github.com/lyleee0083/xiaomi-be7000-openwrt/releases) 下载对应版本的固件文件与 `SHA256SUMS.txt`。刷写前请先备份设备原厂分区（尤其是 `0:ART` 与 `bdata`），并校验文件摘要：

```sh
sha256sum -c SHA256SUMS.txt
```

- **U-Boot Webfailsafe 首次刷入**：刷入 `openwrt-xiaomi-be7000-<版本>-squashfs-factory.ubi`（可配合 [xiaomi-be7000-uboot](https://github.com/lyleee0083/xiaomi-be7000-uboot) 使用）。
- **OpenWrt 系统内升级**：在 LuCI 系统升级页面或通过 `sysupgrade` 使用 `openwrt-xiaomi-be7000-<版本>-squashfs-sysupgrade.bin`。

首次启动默认管理地址为 `http://192.168.1.1`，默认无管理员密码，建议首次登录后立即设置密码。

## 配置

静态出厂默认与运行策略直接集成在源码树中：

- **系统与时间**：[`etc/config/system`](target/linux/qualcommbe/ipq95xx/base-files/etc/config/system) 默认主机名为 `BE7000`，时区为 `CST-8`（`Asia/Shanghai`），NTP 客户端仅启用 `cn.pool.ntp.org`（关闭本地 NTP 服务端与 DHCP NTP），ZRAM 使用 `lzo`（4 流）。
- **指示灯策略**：机身 5 颗 GPIO 指示灯（`white:network`、`amber:network`、`white:system`、`amber:system`、`white:aiot`）在启动完成后默认关闭（`default=0`、`trigger=none`）；4 个 QCA8084 网口绿色链路灯保持 `netdev` 状态指示。
- **网络、连接跟踪与调频**：[`sysctl-nf-conntrack.conf`](package/kernel/linux/files/sysctl-nf-conntrack.conf) 设置 `net.netfilter.nf_conntrack_max=65535`、`buckets=16384`；[`sysctl-tcp-bbr.conf`](package/kernel/linux/files/sysctl-tcp-bbr.conf) 不强制覆盖防火墙保存的 `tcpcca` 拥塞控制选择；[`etc/init.d/boot`](package/base-files/files/etc/init.d/boot) 在模块加载后对支持 `schedutil` 的数字 CPUFreq policy 自动启用并回读校验 `schedutil`，保留内核原生频率边界。
- **构建配置**：[`configs/xiaomi_be7000_defconfig`](configs/xiaomi_be7000_defconfig) 为唯一维护的精简构建配置种子。

## 构建与测试

### 离线结构与行为校验

在任意安装了 Python 3.10+ 的环境中运行离线检查（Linux 环境同时执行 Shell 语法及 MAC/CPUFreq 行为测试）：

```sh
python3 tests/verify_be7000_tree.py
```

### 固件构建（Ubuntu 24.04 x86_64）

准备好 OpenWrt 构建依赖后，执行 [`scripts/build-be7000.sh`](scripts/build-be7000.sh) 更新 feeds、生成并校验 `.config`、编译固件并输出带摘要清单的交付文件：

```sh
./scripts/feeds update -a
./scripts/feeds install -a
./scripts/build-be7000.sh
```

仅验证配置展开而不执行完整编译时，可运行 `./scripts/build-be7000.sh --prepare-config`。构建产物直接输出到 `release/` 目录。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| [`VERSION`](VERSION) | 统一发布版本号，同步写入固件系统信息、交付文件名与 Release 标签 |
| [`configs/xiaomi_be7000_defconfig`](configs/xiaomi_be7000_defconfig) | 小米 BE7000 精简固件配置种子 |
| [`scripts/build-be7000.sh`](scripts/build-be7000.sh) | 配置生成、完整固件构建、版本一致性校验及摘要生成入口 |
| [`target/linux/qualcommbe/`](target/linux/qualcommbe) | Linux 6.18 内核补丁、[`ipq9554-be7000.dts`](target/linux/qualcommbe/dts/ipq9554-be7000.dts) 设备树、镜像规则与板级默认文件 |
| [`package/firmware/ipq-wifi/`](package/firmware/ipq-wifi) | BE7000 的 IPQ9574 与 QCN9274 `board-2.bin` 覆盖包 |
| [`tests/verify_be7000_tree.py`](tests/verify_be7000_tree.py) | 仓库裁剪范围、设备树、MAC 派生、CPUFreq 与文档一致性检查 |
| [`.github/workflows/build-be7000.yml`](.github/workflows/build-be7000.yml) | Pull Request 快速门禁检查、固件自动编译与 GitHub Release 发布工作流 |

## 版本发布

工作流通过校验和完整编译后，根据 [`VERSION`](VERSION) 在 [Releases](https://github.com/lyleee0083/xiaomi-be7000-openwrt/releases) 发布同版本标签 `openwrt-xiaomi-be7000-<版本>`，并直接提供以下已核验文件：

- `openwrt-xiaomi-be7000-<版本>-squashfs-factory.ubi`
- `openwrt-xiaomi-be7000-<版本>-squashfs-sysupgrade.bin`
- `SHA256SUMS.txt`

离线测试与 GitHub Actions 构建成功仅代表源码、镜像封装及受控脚本逻辑通过检查；BE7000 实机启动、恢复出厂、射频表现与长期运行稳定性需另行在硬件上验收。

## 许可证

- OpenWrt / LEDE 主体构建系统与源码遵循 [GNU GPL v2](COPYING)，补充许可证文本见 [`LICENSES/`](LICENSES)。
- 上游源码派生自 [coolsnowwolf/lede](https://github.com/coolsnowwolf/lede)（基线提交 [`bc7f99dd`](https://github.com/coolsnowwolf/lede/commit/bc7f99dd449ac05543d8bbbd42b21ddb33c70cae)）；无线二进制固件包拉取声明与专有许可参见 [`package/firmware/ath-firmware-ddwrt/Makefile`](package/firmware/ath-firmware-ddwrt/Makefile) 及 [`Notice.txt`](package/firmware/ath-firmware-ddwrt/src/ath12k/QCN9274/hw1.0/Notice.txt)。
