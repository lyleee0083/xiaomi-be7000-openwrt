#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$ROOT_DIR"

MODE="full"
JOBS="${JOBS:-$(nproc)}"
if [[ "${1:-}" == "--prepare-config" ]]; then
  MODE="prepare-config"
  shift
fi
if [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--prepare-config]" >&2
  exit 2
fi

VERSION="$(tr -d ' \t\r\n' < VERSION)"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid VERSION '$VERSION' (expected X.Y.Z)." >&2
  exit 1
fi

SHORT_SHA="$(git rev-parse --short=8 HEAD)"
VERSION_CODE="be7000-${SHORT_SHA}"

cp configs/xiaomi_be7000_defconfig .config
cat >> .config <<EOF
CONFIG_VERSION_NUMBER="${VERSION}"
CONFIG_VERSION_CODE="${VERSION_CODE}"
EOF

make defconfig

grep -Fxq 'CONFIG_TARGET_qualcommbe=y' .config
grep -Fxq 'CONFIG_TARGET_qualcommbe_ipq95xx=y' .config
grep -Fxq 'CONFIG_TARGET_qualcommbe_ipq95xx_DEVICE_xiaomi_be7000=y' .config
grep -Fxq 'CONFIG_CPU_TYPE="cortex-a73"' .config
grep -Fxq "CONFIG_VERSION_NUMBER=\"${VERSION}\"" .config
grep -Fxq "CONFIG_VERSION_CODE=\"${VERSION_CODE}\"" .config

for forbidden in \
  default-settings \
  luci-theme-design \
  luci-app-ssr-plus \
  luci-app-upnp \
  luci-app-ddns \
  luci-app-vsftpd \
  luci-app-samba4 \
  luci-app-vlmcsd \
  luci-app-zerotier \
  luci-app-turboacc \
  luci-app-wol \
  luci-app-autoreboot \
  luci-app-filetransfer \
  luci-app-accesscontrol \
  luci-app-arpbind \
  luci-app-nlbwmon; do
  if grep -Eq "^CONFIG_PACKAGE_${forbidden}=(y|m)$" .config; then
    echo "Forbidden bloatware package enabled in .config: ${forbidden}" >&2
    exit 1
  fi
done

echo "Verified .config for Xiaomi BE7000 version ${VERSION} (${VERSION_CODE})."
if [[ "$MODE" == "prepare-config" ]]; then
  exit 0
fi

make download -j"$JOBS"
make -j"$JOBS" || make -j1 V=s

ROOTFS_DIR="build_dir/target-aarch64_cortex-a73_musl/root-qualcommbe"
test -d "$ROOTFS_DIR"
grep -Fxq "DISTRIB_RELEASE='${VERSION}'" "$ROOTFS_DIR/etc/openwrt_release"
grep -Fxq "DISTRIB_REVISION='${VERSION_CODE}'" "$ROOTFS_DIR/etc/openwrt_release"
grep -Fxq "VERSION=\"${VERSION}\"" "$ROOTFS_DIR/usr/lib/os-release"
test -s "$ROOTFS_DIR/lib/firmware/ath11k/IPQ9574/hw1.0/board-2.bin"
test -s "$ROOTFS_DIR/lib/firmware/ath12k/QCN9274/hw2.0/board-2.bin"
test -s "$ROOTFS_DIR/etc/config/system"
test -s "$ROOTFS_DIR/lib/functions/be7000-mac.sh"

BIN_DIR="bin/targets/qualcommbe/ipq95xx"
FACTORY_SRC="$(find "$BIN_DIR" -maxdepth 1 -type f -name '*xiaomi_be7000-squashfs-factory.ubi' | head -n 1)"
SYSUPGRADE_SRC="$(find "$BIN_DIR" -maxdepth 1 -type f -name '*xiaomi_be7000-squashfs-sysupgrade.bin' | head -n 1)"
test -n "$FACTORY_SRC" && test -s "$FACTORY_SRC"
test -n "$SYSUPGRADE_SRC" && test -s "$SYSUPGRADE_SRC"

RELEASE_DIR="$ROOT_DIR/release"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

FACTORY_OUT="openwrt-xiaomi-be7000-${VERSION}-squashfs-factory.ubi"
SYSUPGRADE_OUT="openwrt-xiaomi-be7000-${VERSION}-squashfs-sysupgrade.bin"

cp -f -- "$FACTORY_SRC" "$RELEASE_DIR/$FACTORY_OUT"
cp -f -- "$SYSUPGRADE_SRC" "$RELEASE_DIR/$SYSUPGRADE_OUT"

(
  cd -- "$RELEASE_DIR"
  sha256sum -- "$FACTORY_OUT" "$SYSUPGRADE_OUT" > SHA256SUMS.txt
  sha256sum -c SHA256SUMS.txt
)

echo "Staged verified deliverables in $RELEASE_DIR:"
cat "$RELEASE_DIR/SHA256SUMS.txt"
