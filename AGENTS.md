# xiaomi-be7000-openwrt Repository Instructions

These instructions apply to all agents working in this repository.

## Scope

- Write repository `AGENTS.md` files entirely in English.
- Confirm the repository root, target branch, worktree status, and applicable instructions before editing. Keep changes within the authorized task and preserve existing work.
- Track build source, build configuration and scripts, test and validation code, and essential resources and documentation. Maintained configuration and rule data are source. Keep temporary files in the task directory. Deliver build packages and validation outputs through the project artifact channel when authorized.

## GitHub

### Repository changes

- Make fixes directly in the maintained source code, configuration, or build logic that owns the behavior, including in forks. Do not add patch files, build-time source rewrites, or redundant wrappers as substitutes for direct fixes.
- Start new upstream-based work and upstream updates from the latest commit on the applicable upstream branch. Verify the branch tip remotely and record the upstream repository, branch, and full commit SHA. Use the upstream default branch unless the task specifies another branch or revision.
- Run all repository builds and compilation exclusively in GitHub Actions; do not build or compile locally. Deliver the verified artifacts from the successful workflow run.
- Keep GitHub Actions on the latest stable Linux runner (`ubuntu-latest`) as the sole build and packaging path. Use a different GitHub Actions runner only when the deliverable cannot be built on `ubuntu-latest`.

### GitHub CLI

- Use official `gh` first for GitHub operations. Resolve PATH candidates without executing them. On Windows also check known locations, including `%ProgramFiles%\GitHub CLI\gh.exe`, and available installer records. Before `--version`, verify the actual file using trusted installer evidence binding its path and contents to the installed package, or compare its bytes with the executable from a verified official release package. Product name, publisher text, version, or expected path alone is insufficient. Invoke the verified absolute path; reuse verification only while that path and its SHA-256 match the verified copy. Report a broken installation separately. If absent and writes are permitted, install a verified official package in a task-local tools directory or an explicitly authorized installation directory. Obtain authorization for any other destination. Verify the installed executable and run `--version`.
- Use `gh api` for REST or GraphQL operations without a dedicated command. A connector or browser may handle operations the CLI does not support. For the same authorized read-only operation, use an already authorized connector if `gh` provenance cannot be verified within scope, or if `gh` is confirmed missing, broken, or unable to start and installation or repair is outside scope. Leave an unverified executable unexecuted. Never switch channels to bypass an access denial.

### Pull requests and merges

- Every GitHub repository must have an active `Protect main` ruleset for its default branch. Require pull requests and block branch deletion and force pushes. Require status checks that actually run on pull requests targeting the protected branch.
- Enable and verify **Automatically delete head branches** (`delete_branch_on_merge: true`) in every GitHub repository when creating or configuring it. Before merging a pull request, check the setting on the source repository, including the fork for a fork-based pull request. Enable it when authorized, and report any permission or branch protection rule that prevents automatic deletion. Report any other limitation on automatic branch deletion.
- Before writing to a shared branch, verify the current head and check for competing writers. Follow the repository rules for reviews and checks, and verify the remote commit and source branch cleanup after merging.

### README and Release pages

- Write the primary README and GitHub Release titles and bodies in Simplified Chinese by default, including workflow-generated notes. Follow explicit language requests and keep official names and identifiers. Translate the headings listed below into the document language.
- Start the README with one project-name H1 and a brief overview. Use applicable H2s in the order Features, Quick Start, Configuration, Build and Test, Repository Structure, Releases, and License. Cover prerequisites, installation and basic usage in Quick Start.
- Title each Release `<project> <version>` and open with a short summary. Use applicable H2s in the order Main Changes, Downloads and Verification, Installation and Upgrade, and Verification Status. Identify verified assets and `SHA256SUMS.txt`. Distinguish CI from device or production acceptance.
- Use GitHub Markdown with tagged code fences, relative README file links and tag-pinned Release links to repository files. Verify commands, paths, links and licenses. Omit empty sections and placeholders. Preserve accurate content. Name and link upstreams, record known refs, credit imports and retain license and copyright notices.

## Build and Verification

- Target the Xiaomi BE7000 (`xiaomi,be7000`) exclusively on `qualcommbe/ipq95xx` (Linux 6.18, Armv8.0-A `cortex-a73`). Preserve shared OpenWrt build infrastructure, `target/linux/generic` 6.18 support, `ipq9574-common*.dtsi`, and packages required by this board.
- Use [configs/xiaomi_be7000_defconfig](configs/xiaomi_be7000_defconfig) and [scripts/build-be7000.sh](scripts/build-be7000.sh) as the authoritative configuration and build entry points. Keep the base package set lean (Bootstrap LuCI, FW4/nftables, Qualcomm PPE offload, PPPoE, IPv6, SSH, zram-swap) without proxy, VPN, NAS, UPnP, or KMS bloatware.
- Preserve Xiaomi BE7000 stock ART (`0:art` / `0:ART`) offsets: wired slots `0x0`, `0x6`, `0xc`, `0x12` (with deterministic locally-administered unicast fallback for blank `FF` or colliding slots), 2.4G IPQ9574 calibration at `0x1000` (`0x20000`) with MAC at `0x100e`, and 5G QCN9274 calibration at `0x65000` (`0x2d000`) with MAC at `0x65010`.
- Run `python3 tests/verify_be7000_tree.py` for offline tree, DTS, MAC, CPUFreq, and configuration regressions. The `Verify BE7000 OpenWrt` check covers pull requests to `main`.
- Keep device operations and publication within task authorization, and report offline or CI build verification separately from physical BE7000 boot, factory-reset, RF, and stability acceptance.

## Versioned deliverables

- [VERSION](VERSION) defines the single release version synchronized across `CONFIG_VERSION_NUMBER`, `/etc/openwrt_release`, `/usr/lib/os-release`, direct output filenames (`openwrt-xiaomi-be7000-<version>-squashfs-factory.ubi` and `openwrt-xiaomi-be7000-<version>-squashfs-sysupgrade.bin`), and the GitHub Release tag (`openwrt-xiaomi-be7000-<version>`).
- When a change affects a versioned deliverable, advance [VERSION](VERSION) and rebuild the latest authorized repository state. Record upstream component versions and source revisions separately. Verify the embedded version and checksums in the final artifacts.
- Verify the version at each applicable surface in the actual delivered artifact and refresh its checksums. Build, publication and deployment follow their respective authorization scopes.

## Release asset integrity

- Deliver native usable firmware images directly with `SHA256SUMS.txt`. Publish the same verified build outputs to GitHub Releases with identical filenames and SHA-256 hashes.
- Match the Release tag to the verified build commit. Check every published asset against the delivery files and checksum manifest. Report missing source, build, or Release evidence.
- Use the repository's native format and honor the requested packaging format.
