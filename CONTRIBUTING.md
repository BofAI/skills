# Contributing to BofAI Skills

Thank you for contributing. Read [AGENTS.md](./AGENTS.md) for Skill authoring requirements and
[BRANCHING.md](./BRANCHING.md) for the repository's branch and release model.

## Key branches

- `develop` is the default development and integration branch.
- `main` contains stable, released Skills collections.
- `release_*` branches are release snapshots created from `develop` and merged into `main` after
  regression testing.
- `feature/*` branches contain ordinary work created from `develop`.
- `hotfix/*` branches contain urgent released-version fixes created from `main`.

Do not push directly to `develop` or `main`.

## Fork and clone

Fork `BofAI/skills`, then configure the official repository as `upstream`:

```bash
git clone https://github.com/<your-account>/skills.git
cd skills
git remote add upstream https://github.com/BofAI/skills.git
```

## Synchronize and develop

Synchronize your fork's development branch:

```bash
git fetch upstream
git switch develop
git merge upstream/develop --no-ff
git push origin develop
```

Create an ordinary work branch from `develop`:

```bash
git switch -c feature/<short_description> develop
```

Use the `feature/*` prefix for features, fixes, documentation, tests, refactors, build changes, and
CI changes. Describe the change type in the commit and pull-request title.

## Validate the change

- Ensure every changed `SKILL.md` has valid YAML frontmatter.
- Test the Skill with realistic agent requests.
- Verify examples and scripts work as documented.
- Validate JSON and other resource files.
- Document exact external CLI versions when deterministic behavior matters.
- Review security, secrets, confirmation, network, slippage, and fee behavior.

Follow any repository validation commands documented in `AGENTS.md` or the affected Skill.

## Submit a pull request

Push the branch to your fork and open a pull request targeting `develop`:

```bash
git push origin feature/<short_description>
```

The title must use Conventional Commits, for example:

```text
feat(wallet-cli): add resource delegation guidance
fix(sunswap): validate the configured network
docs: clarify stable installation
```

Keep one pull request focused on one concern. Explain what changed, why it changed, and how it was
verified. Address review feedback and keep the branch synchronized with `develop`.

## Release and hotfix contributions

Maintainers create `release_*` and `hotfix/*` branches. Release branches accept only release
preparation and regression fixes. Hotfix branches accept only urgent corrections for code already
published from `main`. Both must be merged back into `develop`.

## Code of conduct

Be respectful and constructive in all interactions. Open an issue when a substantial new workflow
needs design discussion before implementation.
