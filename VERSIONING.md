# Versioning

This repository uses one release version for the complete Skills collection.

## Source of truth

The root [`VERSION`](./VERSION) file is the source of truth. Its value uses Semantic Versioning
without a leading `v`.

The same version must appear in:

- every top-level `*/SKILL.md` frontmatter `version` field;
- every top-level skill `package.json` that declares a version;
- the root package entries in corresponding `package-lock.json` files;
- the newest entry in `CHANGELOG.md`.

Release tags add the conventional prefix: version `2.0.0` is tagged `v2.0.0`. Do not create
independent per-skill release tags. A change to any skill is released as a new repository version,
and all skill frontmatter versions advance together even when a particular skill did not change.

## Dependency versions

External CLI, SDK, runtime, and service versions are independent of the repository release. Keep
them in each skill's `dependencies`, prerequisites, and installer. Financial execution CLIs should
normally use an exact tested version; use a range only when the skill intentionally supports and
tests that complete range.

For example:

```yaml
version: 2.0.0
dependencies:
  - "@tron-walletcli/wallet-cli@4.13.0"
```

Here `2.0.0` is the BofAI Skills release and `4.13.0` is the independently maintained CLI version.

## Release rules

- Patch: documentation corrections and backward-compatible fixes.
- Minor: backward-compatible skill additions or workflow improvements.
- Major: removed skills, renamed skills, incompatible trigger or workflow changes, or changed
  authorization/security contracts.

Before finalizing a release, update `VERSION`, all skill and package mirrors, and `CHANGELOG.md`,
then run:

```bash
sh scripts/check_versions.sh
```
