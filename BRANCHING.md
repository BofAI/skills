# Branching and Release Workflow

This repository follows the java-tron branching model while retaining `main` as the name of the
stable release branch.

## Key branches

| Branch | Purpose |
|---|---|
| `develop` | Default development and integration branch for the next release |
| `main` | Stable branch containing only released Skills collections |
| `release_vX.Y.Z` | Release snapshot cut from `develop`, regression-tested, and permanently retained |
| `feature/*` | Feature, fix, documentation, test, refactor, or CI work cut from `develop` |
| `hotfix/*` | Urgent fix cut from `main` for an already released version |

Direct pushes to `develop` and `main` are not allowed. Changes enter both branches through reviewed
pull requests.

## Development flow

1. Synchronize a local `develop` branch with `upstream/develop`.
2. Create `feature/<short_description>` from `develop`.
3. Submit the pull request to `develop`.
4. After review and required checks pass, merge it into `develop`.

Use `feature/*` for every ordinary change. The commit and pull-request type still communicates
whether the work is a feature, fix, documentation update, refactor, test, build, or CI change.

## Release flow

1. Create `release_vX.Y.Z` from `develop` when the release scope is frozen.
2. Update the repository and Skill versions, changelog, dependency pins, and release notes there.
3. Run regression, installation, and agent-behavior tests on the release branch.
4. Merge release-blocking fixes directly into `release_vX.Y.Z`; do not add unrelated features.
5. After regression passes, merge `release_vX.Y.Z` into `main` and tag the merge commit `vX.Y.Z`.
6. Merge `release_vX.Y.Z` back into `develop` so every release fix is preserved.
7. Permanently retain the release branch as the source snapshot for that release.

## Hotfix flow

1. Create `hotfix/<short_description>` from `main`.
2. Limit the branch to the released defect and its tests or documentation.
3. Merge the hotfix into `main` and create the corresponding patch release tag.
4. Merge the same hotfix into `develop`.

## Pull-request routing

| Target | Allowed source branches |
|---|---|
| `develop` | `feature/*`, `release_*`, `hotfix/*` |
| `main` | `release_*`, `hotfix/*` |

The `release_*` and `hotfix/*` routes back to `develop` are mandatory. A feature branch must never
target `main` directly.

## Installation channels

Because `develop` is the development branch, public installation instructions must select a stable
source explicitly:

```bash
npx skills add https://github.com/BofAI/skills/tree/main
```

Use the development branch only for intentional pre-release testing:

```bash
npx skills add https://github.com/BofAI/skills/tree/develop
```

For reproducible production installation, prefer a formal version tag when one is available:

```bash
npx skills add https://github.com/BofAI/skills/tree/vX.Y.Z
```

## Required repository settings

Configure GitHub after the bootstrap pull request lands:

- make `develop` the default branch;
- protect `develop` and `main` from direct and force pushes;
- require pull requests, at least one approval, and all required checks;
- require conversation resolution;
- restrict deletion of both long-lived branches;
- allow `main` pull requests only from `release_*` and `hotfix/*` through the branch-policy check.
