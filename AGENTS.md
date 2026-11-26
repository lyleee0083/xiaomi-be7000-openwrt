# xiaomi-be7000-openwrt Repository Instructions

## Scope

- Confirm the repository root, target branch, worktree status, and applicable instructions before editing. Keep changes within the authorized task and preserve existing work.
- Track build source, build configuration and scripts, test and validation code, and essential resources and documentation. Maintained configuration and rule data are source. Keep temporary files in the task directory. Deliver build packages and validation outputs through the project artifact channel when authorized.

## GitHub

- Make fixes directly in the maintained source code, configuration, or build logic that owns the behavior, including in forks. Do not add patch files, build-time source rewrites, or redundant wrappers as substitutes for direct fixes.
- Prefer the verified official `gh`. On Windows, resolve the executable without running it and verify its contents with trusted installer evidence or an official release package. Use the verified absolute path and SHA-256. Use `gh api` for operations without a dedicated command. An authorized connector may perform the same read-only operation if the CLI is unavailable or unverified and repair is outside scope. Respect access denials.
- Every GitHub repository must have an active `Protect main` ruleset for its default branch. Require pull requests and block branch deletion and force pushes. Require status checks that actually run on pull requests targeting the protected branch.
- Enable and verify `delete_branch_on_merge: true` when creating or configuring a repository. Before merging a pull request, verify this setting in its source repository, including a fork, and report any limit on automatic branch deletion.
- Before writing to a shared branch, verify the current head and check for competing writers. Follow the repository rules for reviews and checks, and verify the remote commit and source branch cleanup after merging.
- Maintain one H1 in the primary README, with the project name and purpose. Where applicable, keep the H2 order Features, Quick Start, Configuration, Build and Test, Repository Structure, Releases, and License. Use the established language, fenced code blocks with language identifiers, and relative links for repository files.
- Name and link the upstream repository in the README, and record the source tag or commit when known. Credit imported components in the README or linked third-party notices and preserve applicable license and copyright notices.

## Build and Verification

- Target the Xiaomi BE7000 (`xiaomi,be7000`) exclusively on `qualcommbe/ipq95xx` (Linux 6.18, Armv8.0-A `cortex-a73`). Preserve shared OpenWrt build infrastructure, `target/linux/generic` 6.18 support, `ipq9574-common*.dtsi`, and packages required by this board.
- Use [configs/xiaomi_be7000_defconfig](configs/xiaomi_be7000_defconfig) and [scripts/build-be7000.sh](scripts/build-be7000.sh) as the authoritative configuration and build entry points. Keep the base package set lean (Bootstrap LuCI, FW4/nftables, Qualcomm PPE offload, PPPoE, IPv6, SSH, zram-swap) without proxy, VPN, NAS, UPnP, or KMS bloatware.
- Preserve Xiaomi BE7000 stock ART (`0:art` / `0:ART`) offsets: wired slots `0x0`, `0x6`, `0xc`, `0x12` (with deterministic locally-administered unicast fallback for blank `FF` or colliding slots), 2.4G IPQ9574 calibration at `0x1000` (`0x20000`) with MAC at `0x100e`, and 5G QCN9274 calibration at `0x65000` (`0x2d000`) with MAC at `0x65010`.
- Run `python3 tests/verify_be7000_tree.py` for offline tree, DTS, MAC, CPUFreq, and configuration regressions. The `Verify BE7000 OpenWrt` check covers pull requests to `main`.
- Keep device operations and publication within task authorization, and report offline or CI build verification separately from physical BE7000 boot, factory-reset, RF, and stability acceptance.

## Versioned deliverables

- [VERSION](VERSION) defines the single release version synchronized across `CONFIG_VERSION_NUMBER`, `/etc/openwrt_release`, `/usr/lib/os-release`, direct output filenames (`openwrt-xiaomi-be7000-<version>-squashfs-factory.ubi` and `openwrt-xiaomi-be7000-<version>-squashfs-sysupgrade.bin`), and the GitHub Release tag (`openwrt-xiaomi-be7000-<version>`).
- When a change affects a versioned deliverable, advance [VERSION](VERSION) and rebuild the latest authorized repository state. Record upstream component versions and source revisions separately. Verify the embedded version and checksums in the final artifacts.

## Release asset integrity

- Deliver native usable firmware images directly with `SHA256SUMS.txt`. Publish the same verified build outputs to GitHub Releases with identical filenames and SHA-256 hashes.
- Match the Release tag to the verified build commit. Check every published asset against the delivery files and checksum manifest. Report missing source, build, or Release evidence.
