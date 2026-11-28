# Xiaomi BE7000 OpenWrt Project Requirements

## Board and framework

- Build only for Xiaomi BE7000 (`xiaomi,be7000`) on `qualcommbe/ipq95xx`, ARMv8.0-A Cortex-A73. [The target Makefile](target/linux/qualcommbe/Makefile) owns the kernel line. The `main` target uses Linux 6.18. Treat kernel, target, and board migrations as framework changes.
- Preserve the shared OpenWrt build infrastructure, the matching generic kernel support and IPQ9574 device trees, and packages required by this board.
- Use [the BE7000 defconfig](configs/xiaomi_be7000_defconfig) and [the board build script](scripts/build-be7000.sh) as the configuration and firmware build entry points.
- Keep the base package set lean: Bootstrap LuCI, FW4/nftables, Qualcomm PPE offload, PPPoE, IPv6, SSH, and zram swap. Keep proxy, VPN, NAS, containers, UPnP, and KMS outside the base image.
- Preserve the stock `0:art` / `0:ART` layout: wired slots at `0x0`, `0x6`, `0xc`, and `0x12`, deterministic local-unicast fallback for blank or duplicate slots, 2.4 GHz MAC at `0x100e` and calibration at `0x1000` (length `0x20000`), and 5 GHz MAC at `0x65010` and calibration at `0x65000` (length `0x2d000`).

## Build and acceptance

- Use [Verify BE7000 OpenWrt and Build BE7000 Firmware Images](.github/workflows/build-be7000.yml) for tree, DTS, MAC, CPUFreq, feed and defconfig checks and firmware builds. The current workflow pins Ubuntu 24.04. Runner migration needs verification of feed expansion and both firmware formats.
- [VERSION](VERSION) supplies the version for `CONFIG_VERSION_NUMBER`, `/etc/openwrt_release`, `/usr/lib/os-release`, the factory UBI and sysupgrade BIN filenames, and `openwrt-xiaomi-be7000-<version>` release tag. Deliver the two native images and the checksum manifest.
- Require separate hardware acceptance for boot, factory reset, radios and runtime stability. Firmware builds do not authorize flashing, reboots, or device configuration changes.
