#!/usr/bin/env python3
"""Offline repository scope, hardware layout, and script regression checks for Xiaomi BE7000 OpenWrt."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_BLOAT_PACKAGES = {
    "default-settings",
    "luci-theme-design",
    "luci-app-ssr-plus",
    "luci-app-upnp",
    "luci-app-ddns",
    "luci-app-vsftpd",
    "luci-app-samba4",
    "luci-app-vlmcsd",
    "luci-app-zerotier",
    "luci-app-turboacc",
    "luci-app-wol",
    "luci-app-autoreboot",
    "luci-app-filetransfer",
    "luci-app-accesscontrol",
    "luci-app-arpbind",
    "luci-app-nlbwmon",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_lf_text(rel_path: str) -> str:
    path = ROOT / rel_path
    require(path.is_file(), f"Missing required file: {rel_path}")
    raw = path.read_bytes()
    require(b"\r\n" not in raw, f"CRLF line endings are not permitted in {rel_path}")
    return raw.decode("utf-8")


def verify_scope() -> None:
    targets_dir = ROOT / "target/linux"
    entries = sorted(p.name for p in targets_dir.iterdir())
    require(entries == ["Makefile", "generic", "qualcommbe"], f"Unexpected target/linux entries: {entries}")

    generic_entries = [p.name for p in (targets_dir / "generic").iterdir()]
    bad_generic = [n for n in generic_entries if re.search(r"-(5\.\d+|6\.\d+|7\.(?!3$)\d+)$", n)]
    require(not bad_generic, f"Non-7.3 generic directories left in tree: {bad_generic}")
    qualcommbe_dir = targets_dir / "qualcommbe"
    require("KERNEL_PATCHVER:=7.3" in (qualcommbe_dir / "Makefile").read_text(encoding="utf-8"), "qualcommbe must target KERNEL_PATCHVER:=7.3")
    require((qualcommbe_dir / "config-7.3").is_file() and not (qualcommbe_dir / "config-6.18").exists(), "qualcommbe must use config-7.3 only")
    require((qualcommbe_dir / "patches-7.3").is_dir() and not (qualcommbe_dir / "patches-6.18").exists(), "qualcommbe must use patches-7.3 only")
    require("LINUX_VERSION-7.3 = .6" in (ROOT / "include" / "kernel-7.3").read_text(encoding="utf-8"), "include/kernel-7.3 must track 7.3.6")
    for p in sorted((qualcommbe_dir / "patches-7.3").glob("*.patch")):
        require(b"\r\n" not in p.read_bytes(), f"CRLF detected in {p.relative_to(ROOT)}")

    qbe_dir = targets_dir / "qualcommbe"
    require(not (qbe_dir / "ipq53xx").exists(), "ipq53xx subtarget must be absent")
    require((qbe_dir / "ipq95xx").is_dir(), "ipq95xx subtarget directory missing")

    dts_files = sorted(p.name for p in (qbe_dir / "dts").iterdir() if p.is_file())
    require(
        dts_files == [
            "ipq9554-be7000.dts",
            "ipq9574-common-qca8084.dtsi",
            "ipq9574-common-wifi-ahb.dtsi",
            "ipq9574-common.dtsi",
        ],
        f"Unexpected qualcommbe DTS files: {dts_files}",
    )

    image_files = sorted(p.name for p in (qbe_dir / "image").iterdir() if p.is_file())
    require(image_files == ["Makefile", "ipq95xx.mk"], f"Unexpected qualcommbe image files: {image_files}")

    ipq95_mk = read_lf_text("target/linux/qualcommbe/image/ipq95xx.mk")
    devices = re.findall(r"(?m)^define\s+Device/([^\s]+)$", ipq95_mk)
    require(devices == ["xiaomi_be7000"], f"Expected only Device/xiaomi_be7000, found {devices}")
    require("$(call Device/UbiFit)" in ipq95_mk, "xiaomi_be7000 must build factory.ubi via Device/UbiFit")
    require("ipq-wifi-xiaomi_be7000" in ipq95_mk, "xiaomi_be7000 must select ipq-wifi-xiaomi_be7000")

    qbe_mk = read_lf_text("target/linux/qualcommbe/Makefile")
    require("CPU_TYPE:=cortex-a73" in qbe_mk, "qualcommbe Makefile must target cortex-a73")
    require("SUBTARGETS:=ipq95xx" in qbe_mk, "qualcommbe Makefile must restrict SUBTARGETS to ipq95xx")

    target_mk = read_lf_text("include/target.mk")
    require("CPU_CFLAGS_cortex-a73 = -mcpu=cortex-a73" in target_mk, "include/target.mk lacks cortex-a73 CFLAGS")
    router_match = re.search(r"DEFAULT_PACKAGES\.router:=(?:.*\\\n)*.*", target_mk)
    require(router_match is not None, "DEFAULT_PACKAGES.router missing in include/target.mk")
    router_block = router_match.group(0)
    for pkg in FORBIDDEN_BLOAT_PACKAGES:
        require(pkg not in router_block, f"Bloatware package {pkg} still present in DEFAULT_PACKAGES.router")

    ipq_wifi_mk = read_lf_text("package/firmware/ipq-wifi/Makefile")
    require("ALLWIFIBOARDS := xiaomi_be7000" in ipq_wifi_mk, "ipq-wifi must target only xiaomi_be7000")
    require("[ ! -d ./files/ ] || $(CP) ./files/. $(PKG_BUILD_DIR)/" in ipq_wifi_mk, "ipq-wifi must stage ./files/ into PKG_BUILD_DIR")
    wifi_files = sorted(p.name for p in (ROOT / "package/firmware/ipq-wifi/files").iterdir())
    require(
        wifi_files == ["board-xiaomi_be7000.ipq9574", "board-xiaomi_be7000.qcn9274"],
        f"Unexpected ipq-wifi board files: {wifi_files}",
    )
    for wf in wifi_files:
        require((ROOT / "package/firmware/ipq-wifi/files" / wf).stat().st_size > 0, f"Empty board file: {wf}")

    require(not (ROOT / "target/linux/qualcommbe/ipq95xx/base-files/etc/board.d/01_leds").exists(), "01_leds must be retired")
    require(not (ROOT / "README_EN.md").exists() and not (ROOT / "README_JA.md").exists(), "Legacy upstream READMEs must be removed")
    require(not (ROOT / ".github/workflows/openwrt-ci.yml").exists(), "Legacy openwrt-ci.yml must be removed")


def verify_dts_and_defaults() -> None:
    dts = read_lf_text("target/linux/qualcommbe/dts/ipq9554-be7000.dts")
    require(dts.count("{") == dts.count("}"), "Unbalanced braces in ipq9554-be7000.dts")
    expected_bindings = [
        r'&ppe_port1\s*\{[^}]*label\s*=\s*"wan";[^}]*nvmem-cells\s*=\s*<&macaddr_art_0\s+0>;',
        r'&ppe_port2\s*\{[^}]*label\s*=\s*"lan1";[^}]*nvmem-cells\s*=\s*<&macaddr_art_6\s+0>;',
        r'&ppe_port3\s*\{[^}]*label\s*=\s*"lan2";[^}]*nvmem-cells\s*=\s*<&macaddr_art_c\s+0>;',
        r'&ppe_port4\s*\{[^}]*label\s*=\s*"lan3";[^}]*nvmem-cells\s*=\s*<&macaddr_art_12\s+0>;',
        r'wifi1:\s*pcie@0\s*\{[^}]*nvmem-cells\s*=\s*<&macaddr_art_65010\s+0>;',
        r'&wifi0\s*\{[^}]*nvmem-cells\s*=\s*<&macaddr_art_100e\s+0>,\s*<&caldata_art_1000>;',
    ]
    for pat in expected_bindings:
        require(re.search(pat, dts, re.S) is not None, f"Missing expected DTS binding matching: {pat}")
    require("<&macaddr_art_0 1>" not in dts, "Duplicate <&macaddr_art_0 1> LAN MAC assignment must not exist")

    cal_script = read_lf_text("target/linux/qualcommbe/ipq95xx/base-files/etc/hotplug.d/firmware/11-ath12k-caldata")
    require("0x65000 0x2d000" in cal_script, "11-ath12k-caldata must extract QCN9274 caldata at 0x65000 (0x2d000)")

    sys_cfg = read_lf_text("target/linux/qualcommbe/ipq95xx/base-files/etc/config/system")
    for token in (
        "option hostname 'BE7000'",
        "option timezone 'CST-8'",
        "option zonename 'Asia/Shanghai'",
        "option zram_comp_algo 'lzo'",
        "option zram_comp_streams '4'",
        "option enable_server '0'",
        "option use_dhcp '0'",
        "list server 'cn.pool.ntp.org'",
    ):
        require(token in sys_cfg, f"Missing system default: {token}")
    for panel_led in ("white:network", "amber:network", "white:system", "amber:system", "white:aiot"):
        pattern = rf"option sysfs '{re.escape(panel_led)}'\s+option default '0'\s+option trigger 'none'"
        require(re.search(pattern, sys_cfg) is not None, f"Panel LED {panel_led} must default to 0/none")

    conntrack = read_lf_text("package/kernel/linux/files/sysctl-nf-conntrack.conf")
    require("net.netfilter.nf_conntrack_max=65535" in conntrack, "nf_conntrack_max must be 65535")
    require("net.netfilter.nf_conntrack_buckets=16384" in conntrack, "nf_conntrack_buckets must be 16384")

    bbr = read_lf_text("package/kernel/linux/files/sysctl-tcp-bbr.conf")
    require("tcp_congestion_control=bbr" not in bbr, "sysctl-tcp-bbr.conf must not override firewall tcpcca")

    boot_init = read_lf_text("package/base-files/files/etc/init.d/boot")
    require("be7000_select_schedutil" in boot_init, "etc/init.d/boot must invoke be7000_select_schedutil")

    defconfig = read_lf_text("configs/xiaomi_be7000_defconfig")
    require("CONFIG_TARGET_qualcommbe_ipq95xx_DEVICE_xiaomi_be7000=y" in defconfig, "defconfig missing BE7000 target")
    require("CONFIG_IMAGEOPT=y" in defconfig and "CONFIG_VERSIONOPT=y" in defconfig, "defconfig must enable IMAGEOPT and VERSIONOPT")
    require("CONFIG_PACKAGE_luci-theme-bootstrap=y" in defconfig, "defconfig must enable Bootstrap theme")
    for pkg in FORBIDDEN_BLOAT_PACKAGES:
        require(f"CONFIG_PACKAGE_{pkg}=y" not in defconfig, f"defconfig must not enable {pkg}")


def verify_version_and_docs() -> None:
    version = read_lf_text("VERSION").strip()
    require(bool(re.fullmatch(r"\d+\.\d+\.\d+", version)), f"Invalid VERSION format: {version!r}")

    agents = read_lf_text("AGENTS.md")
    require("Protect main" in agents and "delete_branch_on_merge: true" in agents, "AGENTS.md missing GitHub rules")

    readme = read_lf_text("README.md")
    h1s = re.findall(r"(?m)^# .+$", readme)
    require(len(h1s) == 1, f"README.md must have exactly one H1, found {len(h1s)}")
    h2s = re.findall(r"(?m)^## (.+)$", readme)
    expected_h2s = ["功能", "快速开始", "配置", "构建与测试", "仓库结构", "版本发布", "许可证"]
    require(h2s == expected_h2s, f"README.md H2 headings {h2s} != expected {expected_h2s}")
    require("https://github.com/coolsnowwolf/lede" in readme and "bc7f99dd" in readme, "README.md must credit upstream and baseline commit")

    for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)", readme):
        clean = target.split("#", 1)[0]
        require((ROOT / clean).exists(), f"Broken relative link in README.md: {target}")

    for script in (
        "scripts/build-be7000.sh",
        "target/linux/qualcommbe/ipq95xx/base-files/etc/board.d/02_network",
        "target/linux/qualcommbe/ipq95xx/base-files/etc/hotplug.d/firmware/11-ath12k-caldata",
        "target/linux/qualcommbe/ipq95xx/base-files/etc/uci-defaults/14-be7000-mac",
        "target/linux/qualcommbe/ipq95xx/base-files/lib/functions/be7000-mac.sh",
        "target/linux/qualcommbe/ipq95xx/base-files/lib/upgrade/platform.sh",
        "package/boot/uboot-envtools/files/qualcommbe",
        ".github/workflows/build-be7000.yml",
    ):
        read_lf_text(script)


def verify_wireless_ppe_offload() -> None:
    gro_patch = read_lf_text(
        "package/kernel/mac80211/patches-qualcommbe/subsys/395-01-wifi-mac80211-default-AP-GRO-off-for-PPE.patch"
    )
    require("IS_ENABLED(CONFIG_QCOM_PPE)" in gro_patch, "395-01 patch must check IS_ENABLED(CONFIG_QCOM_PPE)")
    require("CONFIG_QCOM_80211AX_PPE" not in gro_patch, "Dead CONFIG_QCOM_80211AX_PPE symbol must not remain in 395-01 patch")

    ath_qbe = read_lf_text("package/kernel/mac80211/ath-qualcommbe.mk")
    require("CONFIG_PACKAGE_kmod-qcom-ppe" in ath_qbe, "ath-qualcommbe.mk must track CONFIG_PACKAGE_kmod-qcom-ppe")
    require("ATH12K_PPE_DS_SUPPORT" in ath_qbe, "ath-qualcommbe.mk must enable ATH12K_PPE_DS_SUPPORT on qualcommbe")

    ath11k_block = re.search(r"define KernelPackage/ath11k\n(.*?)\nendef", ath_qbe, re.S)
    require(ath11k_block is not None, "Missing KernelPackage/ath11k definition in ath-qualcommbe.mk")
    require("AUTOLOAD:=$(call AutoProbe,ath11k)" in ath11k_block.group(1), "KernelPackage/ath11k must set AUTOLOAD for modparams emission")
    require("MODPARAMS.ath11k:=frame_mode=2" in ath11k_block.group(1), "KernelPackage/ath11k must enable frame_mode=2")

    ath11k_ahb_block = re.search(r"define KernelPackage/ath11k-ahb\n(.*?)\nendef", ath_qbe, re.S)
    require(ath11k_ahb_block is not None, "Missing KernelPackage/ath11k-ahb definition in ath-qualcommbe.mk")
    require("+TARGET_qualcommbe:kmod-qcom-ppe" in ath11k_ahb_block.group(1), "KernelPackage/ath11k-ahb must depend on kmod-qcom-ppe")

    ath12k_block = re.search(r"define KernelPackage/ath12k\n(.*?)\nendef", ath_qbe, re.S)
    require(ath12k_block is not None, "Missing KernelPackage/ath12k definition in ath-qualcommbe.mk")
    require("+TARGET_qualcommbe:kmod-qcom-ppe" in ath12k_block.group(1), "KernelPackage/ath12k must depend on kmod-qcom-ppe")

    mac_sh = read_lf_text("package/kernel/mac80211/files/lib/netifd/wireless/mac80211.sh")
    require("mac80211_reload_firewall()" in mac_sh, "mac80211.sh must define mac80211_reload_firewall()")
    setup_block = re.search(r"drv_mac80211_setup\(\) \{(.*?)\n\}", mac_sh, re.S)
    teardown_block = re.search(r"drv_mac80211_teardown\(\) \{(.*?)\n\}", mac_sh, re.S)
    require(setup_block is not None and "mac80211_reload_firewall" in setup_block.group(1), "drv_mac80211_setup must call mac80211_reload_firewall")
    require(teardown_block is not None and "mac80211_reload_firewall" in teardown_block.group(1), "drv_mac80211_teardown must call mac80211_reload_firewall")

    fw4_mk = read_lf_text("package/network/config/firewall4/Makefile")
    require("HW_OFFLOAD_FIXES:=" in fw4_mk and "CONFIG_TARGET_qualcommbe" in fw4_mk, "firewall4 Makefile must enable HW_OFFLOAD_FIXES on qualcommbe")
    require("./files/20-firewall-net.hotplug $(1)/etc/hotplug.d/net/20-firewall" in fw4_mk, "firewall4 Makefile must install 20-firewall net hotplug")

    hotplug = read_lf_text("package/network/config/firewall4/files/20-firewall-net.hotplug")
    require('/usr/sbin/fw4 -q reload' in hotplug, "20-firewall-net.hotplug must reload fw4")

    sr_patches = sorted(p.name for p in (ROOT / "package/network/config/firewall4/patches/sr1010").glob("*.patch"))
    for prefix in ("010-", "020-", "030-", "040-"):
        matches = [n for n in sr_patches if n.startswith(prefix)]
        require(len(matches) == 1, f"Expected firewall4 offload patch starting with {prefix}, found {sr_patches}")
        read_lf_text(f"package/network/config/firewall4/patches/sr1010/{matches[0]}")

    libbpf_mk = read_lf_text("package/libs/libbpf/Makefile")
    require(
        "ARM64_U128_UAPI_FIX:=" in libbpf_mk
        and "CONFIG_TARGET_qualcommbe" in libbpf_mk
        and "ifneq ($(ARM64_U128_UAPI_FIX),)" in libbpf_mk,
        "libbpf Makefile must enable ARM64_U128_UAPI_FIX on qualcommbe/Linux 7.3 ARM64",
    )
    libbpf_u128 = read_lf_text("package/libs/libbpf/patches/sr1010/100-linux-u128-types.patch")
    require("typedef unsigned __int128 __u128" in libbpf_u128, "libbpf 100-linux-u128-types.patch missing __u128")

    hunk_re = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
    for patch_rel in (
        "package/libs/libbpf/patches/100-bpf_tc_classid.patch",
        "package/libs/libbpf/patches/sr1010/100-linux-u128-types.patch",
        *(f"package/network/config/firewall4/patches/sr1010/{n}" for n in sr_patches),
    ):
        plines = read_lf_text(patch_rel).splitlines()
        idx = 0
        while idx < len(plines):
            m = hunk_re.match(plines[idx])
            if not m:
                idx += 1
                continue
            old_exp = int(m.group(1)) if m.group(1) is not None else 1
            new_exp = int(m.group(2)) if m.group(2) is not None else 1
            old_act = new_act = 0
            hunk_start = idx + 1
            idx += 1
            while idx < len(plines):
                line = plines[idx]
                if hunk_re.match(line) or line.startswith(("diff --git ", "--- ")):
                    break
                if old_act == old_exp and new_act == new_exp and (line == "" or line.startswith("-- ")):
                    break
                if line.startswith("+"):
                    new_act += 1
                elif line.startswith("-"):
                    old_act += 1
                elif line.startswith(" ") or line == "":
                    old_act += 1
                    new_act += 1
                elif not line.startswith("\\"):
                    break
                idx += 1
            require(
                old_act == old_exp and new_act == new_exp,
                f"Malformed hunk in {patch_rel}:{hunk_start}: expected -{old_exp},+{new_exp}, got -{old_act},+{new_act}",
            )

    build_sh = read_lf_text("scripts/build-be7000.sh")
    for token in (
        "CONFIG_PACKAGE_kmod-qcom-ppe=y",
        "CONFIG_PACKAGE_kmod-ath11k-ahb=y",
        "CONFIG_PACKAGE_kmod-ath12k=y",
        "ath11k frame_mode=2",
        "20-firewall",
    ):
        require(token in build_sh, f"scripts/build-be7000.sh missing PPE/wireless assertion: {token}")


def run_posix_shell_tests() -> None:
    if os.name == "nt" or shutil.which("sh") is None or shutil.which("hexdump") is None:
        return

    shell_scripts = [
        "scripts/build-be7000.sh",
        "target/linux/qualcommbe/ipq95xx/base-files/etc/board.d/02_network",
        "target/linux/qualcommbe/ipq95xx/base-files/etc/hotplug.d/firmware/11-ath12k-caldata",
        "target/linux/qualcommbe/ipq95xx/base-files/etc/uci-defaults/14-be7000-mac",
        "target/linux/qualcommbe/ipq95xx/base-files/lib/functions/be7000-mac.sh",
        "target/linux/qualcommbe/ipq95xx/base-files/lib/upgrade/platform.sh",
        "package/boot/uboot-envtools/files/qualcommbe",
        "package/base-files/files/etc/init.d/boot",
        "package/kernel/mac80211/files/lib/netifd/wireless/mac80211.sh",
        "package/network/config/firewall4/files/20-firewall-net.hotplug",
    ]
    for rel in shell_scripts:
        interpreter = "bash" if rel.endswith(".sh") and rel.startswith("scripts/") else "sh"
        subprocess.run([interpreter, "-n", str(ROOT / rel)], check=True)

    with tempfile.TemporaryDirectory(prefix="be7000-test-") as tmp:
        tmp_path = Path(tmp)
        # Build synthetic 512 KiB ART image with stock BE7000 pattern:
        # slot0..2 valid unicast, slot3 = FF..FF, 0x100e and 0x65010 valid wireless MACs
        art = bytearray(b"\xff" * 0x70000)
        art[0:6] = bytes.fromhex("28d127100001")
        art[6:12] = bytes.fromhex("28d127a10010")
        art[12:18] = bytes.fromhex("28d127a10011")
        # slot 3 (18..24) left FF:FF:FF:FF:FF:FF
        art[0x100E:0x1014] = bytes.fromhex("28d127a10012")
        art[0x65010:0x65016] = bytes.fromhex("28d127b20020")
        art_file = tmp_path / "art.bin"
        art_file.write_bytes(art)

        harness = tmp_path / "mac_harness.sh"
        harness.write_text(
            f"""#!/bin/sh
set -eu
macaddr_canonicalize() {{
    echo "$1" | tr 'A-F' 'a-f'
}}
macaddr_add() {{
    python3 - "$1" "$2" <<'PY'
import sys
base = int(sys.argv[1].replace(":", ""), 16)
step = int(sys.argv[2])
val = (base + step) & ((1 << 48) - 1)
h = f"{{val:012x}}"
print(":".join(h[i:i+2] for i in range(0, 12, 2)))
PY
}}
logger() {{ :; }}
export BE7000_ART_FILE="{art_file}"
. "{ROOT / 'target/linux/qualcommbe/ipq95xx/base-files/lib/functions/be7000-mac.sh'}"
be7000_load_port_macs ""
printf '%s\\n%s\\n%s\\n%s\\n' "$BE7000_MAC0" "$BE7000_MAC1" "$BE7000_MAC2" "$BE7000_MAC3"
""",
            encoding="utf-8",
        )
        out = subprocess.check_output(["sh", str(harness)], text=True).strip().splitlines()
        require(len(out) == 4 and len(set(out)) == 4, f"Expected 4 distinct MACs, got {out}")
        require(out[0] == "28:d1:27:10:00:01", f"Unexpected WAN MAC: {out[0]}")
        require(out[1] == "28:d1:27:a1:00:10", f"Unexpected LAN1 MAC: {out[1]}")
        require(out[2] == "28:d1:27:a1:00:11", f"Unexpected LAN2 MAC: {out[2]}")
        # Derived slot3 must be locally administered unicast ((0x28 | 2) = 0x2a) and not collide with wifi MACs
        first_octet = int(out[3].split(":")[0], 16)
        require((first_octet & 1) == 0 and (first_octet & 2) == 2, f"Slot3 fallback not local unicast: {out[3]}")
        require(out[3] not in {"28:d1:27:a1:00:12", "28:d1:27:b2:00:20"}, f"Slot3 collided with Wi-Fi MAC: {out[3]}")

        # Test be7000_select_schedutil against simulated cpufreq policies without touching limits
        cpufreq_root = tmp_path / "cpufreq"
        for idx, avail in ((0, "performance powersave schedutil"), (1, "performance powersave")):
            pdir = cpufreq_root / f"policy{idx}"
            pdir.mkdir(parents=True)
            (pdir / "scaling_available_governors").write_text(avail + "\n", encoding="utf-8")
            (pdir / "scaling_governor").write_text("performance\n", encoding="utf-8")
            (pdir / "scaling_max_freq").write_text("1488000\n", encoding="utf-8")

        boot_text = read_lf_text("package/base-files/files/etc/init.d/boot")
        func_match = re.search(r"be7000_select_schedutil\(\) \{.*?\n\}\n", boot_text, re.S)
        require(func_match is not None, "Could not extract be7000_select_schedutil function")
        cpu_harness = tmp_path / "cpu_harness.sh"
        cpu_harness.write_text(
            "#!/bin/sh\nset -eu\nlogger() { :; }\n"
            + func_match.group(0)
            + f'\nbe7000_select_schedutil "{cpufreq_root}"\n',
            encoding="utf-8",
        )
        subprocess.run(["sh", str(cpu_harness)], check=True)
        require((cpufreq_root / "policy0/scaling_governor").read_text().strip() == "schedutil", "policy0 did not switch to schedutil")
        require((cpufreq_root / "policy1/scaling_governor").read_text().strip() == "performance", "policy1 without schedutil must stay unchanged")
        require((cpufreq_root / "policy0/scaling_max_freq").read_text().strip() == "1488000", "scaling_max_freq must stay untouched")

        mac_text = read_lf_text("package/kernel/mac80211/files/lib/netifd/wireless/mac80211.sh")
        reload_match = re.search(r"mac80211_reload_firewall\(\) \{.*?\n\}\n", mac_text, re.S)
        require(reload_match is not None, "Could not extract mac80211_reload_firewall function")
        reload_body = reload_match.group(0)
        fw_state = tmp_path / "fw4.state"
        fw_calls = tmp_path / "fw4.calls"
        fw_bin = tmp_path / "fw4.sh"
        fw_init = tmp_path / "firewall.init"
        fw_bin.write_text(f"#!/bin/sh\necho \"$*\" >> \"{fw_calls}\"\n", encoding="utf-8")
        fw_init.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fw_bin.chmod(0o755)
        fw_init.chmod(0o755)
        patched_body = (
            reload_body
            .replace("/var/run/fw4.state", str(fw_state))
            .replace("/usr/sbin/fw4", str(fw_bin))
            .replace("/etc/init.d/firewall", str(fw_init))
        )
        fw_harness = tmp_path / "fw_reload_harness.sh"
        fw_harness.write_text(
            "#!/bin/sh\nset -eu\n" + patched_body + "\nmac80211_reload_firewall\n",
            encoding="utf-8",
        )
        subprocess.run(["sh", str(fw_harness)], check=True)
        require(not fw_calls.exists(), "mac80211_reload_firewall must skip reload when fw4.state is absent")
        fw_state.write_text("ready\n", encoding="utf-8")
        subprocess.run(["sh", str(fw_harness)], check=True)
        require(fw_calls.read_text(encoding="utf-8").strip() == "-q reload", "mac80211_reload_firewall must invoke fw4 -q reload when ready")


def main() -> int:
    verify_scope()
    verify_dts_and_defaults()
    verify_version_and_docs()
    verify_wireless_ppe_offload()
    run_posix_shell_tests()
    print("All Xiaomi BE7000 OpenWrt tree and configuration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
