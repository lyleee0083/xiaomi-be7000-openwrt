# Agent Instructions

These rules apply to every agent and worker contributing to this repository. Keep this file in English.

## Scope

- Read [PROJECT.md](PROJECT.md) and any applicable nested instructions before planning, editing, reviewing, or building. Treat `PROJECT.md` as the source of project-specific constraints. Update it with an authorized change to the project's scope, architecture, platforms, build, or verification.
- Work in the authorized repository or worktree. Confirm the target branch, current head, and working tree before editing. Preserve existing work. Resolve paths, links, and directory boundaries before writing or deleting. Keep source, tests, and essential documentation in version control, and keep outputs, caches, and task records in their assigned artifact or task directories.
- Keep delegated work within the same authorization. Assign distinct ownership, pass the applicable rules and acceptance criteria, and leave final verification to the coordinating agent.

## Code simplicity and interface ergonomics

- Keep all maintained code as simple and lightweight as practical. Prefer direct solutions and existing primitives. Remove unnecessary code, abstractions, dependencies, duplicated work, and resource use. Preserve required behavior, compatibility, and verification. Measure material size, memory, or performance changes when practical.
- Apply ergonomic principles to every visible interface and interaction. Group related controls, use familiar labels and icons, and give text and controls readable sizes, sufficient contrast, and adequate space. Keep keyboard operation and focus predictable. Show current values, disabled states, and action feedback clearly. Check affected layouts at supported narrow sizes and display scales, and in supported themes. Make repeated actions easy to reach and protect destructive actions against accidental activation.

## Repository changes

- Fix the maintained source or configuration that owns the behavior. Do not add patch files, build-time source rewrites, or redundant wrappers as substitutes for a direct fix. Keep non-default branches limited to variant files and required metadata. Maintain shared files on the default branch and reuse them across variants.
- Start upstream updates from the latest commit on the applicable upstream branch. Verify its remote tip and record the repository, branch, and full commit SHA. Preserve source attribution, licenses, and copyright notices.
- Use verified official `gh` first for GitHub operations and use `gh api` when there is no dedicated command. Verify the Windows executable path and contents from trusted installer evidence or the official distribution before execution. Respect access denials.
- Maintain an active `Protect main` ruleset on the default branch. Require pull requests and status checks that run on those PRs, and block deletion and force pushes. Enable `delete_branch_on_merge: true` when creating or configuring repositories and verify the source repository's setting before merging. Check for competing writers, verify the current head, and confirm the merge commit and branch cleanup afterward.

## Build, verification, and delivery

- Run repository builds and compilation exclusively in GitHub Actions on `ubuntu-latest`. Use a different runner only when the deliverable requires it and document the reason in `PROJECT.md`. Follow the project-specific build, test, and acceptance requirements. Keep CI evidence distinct from physical device or production acceptance.
- When using PowerShell, maintain Windows PowerShell 5.1 and PowerShell 7 compatibility. Keep native output streams and binary data intact, and check each native command's exit code before using its result.
- Advance versions according to the project's rules when deliverables change. Verify the version in applicable filenames, packaging, and the application. Record upstream versions and revisions separately. Deliver the verified native files and `SHA256SUMS.txt`. Match published assets by filename and SHA-256 to the verified build outputs and confirm the release tag points to the build commit. Follow the separate authorization for publication and deployment.

## README and release notes

- Use Simplified Chinese for the primary README and release titles and bodies unless requested otherwise. Use translated headings, tagged code fences, relative README links, and tag-pinned release links. Verify paths, commands, links, and license notices.
- Start the README with one project-name H1 and a short overview. Use applicable H2s in this order: Features, Quick Start, Configuration, Build and Test, Repository Structure, Releases, and License.
- Title releases `<project> <version>`. Start with a short summary and use applicable H2s in this order: Main Changes, Downloads and Verification, Installation and Upgrade, and Verification Status. Identify the actual assets and checksums and state the verification scope.
