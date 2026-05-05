# Contributing to fastapi-hotwire

Thanks for thinking about contributing! Issues and PRs are welcome — please file an issue first for anything bigger than a typo or a docs fix so we can align on scope before you write code.

## Local setup

You'll need [`uv`](https://docs.astral.sh/uv/) installed.

```bash
git clone https://github.com/socialpyre/fastapi-hotwire.git
cd fastapi-hotwire
uv sync --all-extras --group dev
uv run pytest
```

Optionally install pre-commit hooks (recommended — they catch the same things CI does, before you push):

```bash
uv tool install pre-commit
pre-commit install
```

## What runs in CI

- `uvx ruff check .` — lint (errors, unused imports, comprehension issues, modern-Python suggestions).
- `uvx ruff format --check .` — formatting.
- `uvx ty check .` — type checking.
- `uv run pytest` — the test suite, on Python 3.10, 3.11, 3.12, and 3.13.

If any of these fail locally, they'll fail in CI. Fix them before opening the PR.

## Conventional Commits

Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) spec, because [`python-semantic-release`](https://python-semantic-release.readthedocs.io/) uses them to compute the next version and the changelog automatically.

Use one of these types:

| Type | Effect on version | When to use |
| --- | --- | --- |
| `feat:` | minor bump | New user-facing feature. |
| `fix:` | patch bump | Bug fix. |
| `perf:` | patch bump | Performance improvement (no behavior change). |
| `docs:` | none | README, docstrings, examples. |
| `chore:` | none | Tooling, dependencies, refactor without behavior change. |
| `ci:` | none | CI / build / release plumbing. |
| `test:` | none | Tests only. |
| `refactor:` | none | Internal restructure with no behavior change. |

Add `BREAKING CHANGE:` in the commit body (or `feat!:` / `fix!:` in the subject) for anything that breaks the public API. That triggers a major bump.

Keep the subject under ~70 characters and in the imperative mood: `feat: add render_block status_code arg`, not `Added a status code argument`.

The pre-commit hook validates this on every commit. CI also re-validates on PR.

## Tests

- Every feature commit needs a test. The existing test files are organized one-per-module — keep that pattern.
- Tests use `httpx`/`fastapi.testclient.TestClient` against an in-process FastAPI app. No live server needed.
- For Hotwire-shaped responses, use the helpers from `fastapi_hotwire.testing` (`assert_turbo_stream`, `parse_streams`, `assert_turbo_frame`, `turbo_frame_request`, `turbo_stream_request`) rather than asserting on raw HTML.
- Run a single file with `uv run pytest tests/test_streams.py`, a single test with `-k partial_name`.

## Scope

This library is intentionally small and focused. Before proposing a new public API, check it against the [Non-goals](README.md#non-goals) section of the README. Things like WebSocket push, observability, and JS bundling are explicitly **not** in scope and won't be added.

If you're unsure whether something fits, open an issue describing the use case before implementing.

## Releasing (maintainers only)

Releases are fully automated. A push to `main` runs `python-semantic-release`, which:

1. Reads commits since the last tag, computes the next version (`feat:` → minor, `fix:` → patch, `BREAKING CHANGE` → major).
2. Updates `pyproject.toml` and `CHANGELOG.md`, commits, tags `vX.Y.Z`.
3. Builds the wheel + sdist and uploads to PyPI via Trusted Publishing (OIDC — no API tokens).
4. Creates a GitHub Release with the generated changelog entry.

If a push has only `chore:` / `docs:` / `ci:` / `test:` / `refactor:` commits, no release is cut. That's intentional.

## Repo configuration (maintainer setup)

This section is a one-time runbook for whoever provisions the public GitHub repo. Contributors don't need to read it. The configuration here is what was applied to `socialpyre/fastapi-hotwire` and is a sensible default for future Pyre OSS projects.

All steps assume you have `gh` authenticated against an account with admin on the repo.

### 1. Repo metadata

| What | Why | How |
| --- | --- | --- |
| Description | One-sentence summary that surfaces in GitHub search and the repo card | `gh repo edit socialpyre/fastapi-hotwire --description "..."` |
| Homepage URL | Sends visitors to PyPI for install instructions | `gh repo edit socialpyre/fastapi-hotwire --homepage "https://pypi.org/project/fastapi-hotwire/"` |
| Topics | Discoverability — GitHub topic pages and search filters | `gh repo edit socialpyre/fastapi-hotwire --add-topic fastapi --add-topic hotwire --add-topic turbo --add-topic python --add-topic jinja2 --add-topic server-rendered --add-topic stimulus --add-topic web-framework` |
| Disable Wiki | Unused; Wiki collects spam if left open | `gh repo edit socialpyre/fastapi-hotwire --enable-wiki=false` |
| Disable Projects | Unused | `gh repo edit socialpyre/fastapi-hotwire --enable-projects=false` |

### 2. Branch protection on `main`

The release workflow pushes a `chore(release): X.Y.Z [skip ci]` commit and a `vX.Y.Z` tag directly to `main`. **Requiring PRs would break that flow.** The baseline below protects history without blocking the bot.

| Rule | Effect |
| --- | --- |
| Disallow force push | Prevents history rewrites; protects against accidental rebase-on-main |
| Disallow deletion | Prevents the branch being deleted from the UI |
| Require signed commits | Provenance — every commit on `main` is GPG/SSH-signed by either the maintainer or GitHub's bot identity |
| Require linear history | Keeps `git log` readable; matches semantic-release's single-commit release pattern |

Apply via the GitHub UI (Settings → Branches → Add rule) or via `gh api`:

```bash
gh api -X PUT repos/socialpyre/fastapi-hotwire/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks=null \
  -f enforce_admins=false \
  -f required_pull_request_reviews=null \
  -f restrictions=null \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F required_linear_history=true \
  -F required_signatures=true
```

If you ever want to require status checks on direct pushes to `main` too, switch from "Branch protection rules" to "Rulesets" — they apply to all pushes, not just PRs.

### 3. Security and supply chain

In **Settings → Code security**, enable:

- **Dependabot version updates** — already configured via `.github/dependabot.yml` (weekly pip + github-actions). Toggling this on is what activates the schedule.
- **Dependabot security updates** — auto-PRs for known vulnerable deps.
- **Secret scanning** + **Push protection** — blocks commits that contain credential-shaped tokens.
- **Code scanning** — already configured via `.github/workflows/codeql.yml`. Toggling this on enables the Security tab to display findings.
- **Private vulnerability reporting** — enables the "Report a vulnerability" form referenced in `SECURITY.md`.

These are all UI toggles; there's no `gh` equivalent for some of them yet.

### 4. GitHub Environments

The release workflow targets a `pypi` environment so PyPI Trusted Publishing's OIDC handshake has a deployment-context to bind to.

In **Settings → Environments → New environment**, create:

| Name | Configuration |
| --- | --- |
| `pypi` | Deployment branches: **Selected branches** → `main` only. Required reviewers: optional (one for safety, zero for automation). |

### 5. PyPI Trusted Publisher

Confirm the publisher binding at https://pypi.org/manage/account/publishing/. The pending publisher must specify:

| Field | Value |
| --- | --- |
| PyPI project | `fastapi-hotwire` |
| Owner | `socialpyre` |
| Repository | `fastapi-hotwire` |
| Workflow | `release.yml` |
| Environment | `pypi` |

Once the first release runs, the pending publisher is converted to a real publisher and stays bound.

### 6. Verification

After all of the above:

```bash
gh repo view socialpyre/fastapi-hotwire --json description,homepageUrl,repositoryTopics,hasWikiEnabled,hasProjectsEnabled
gh api repos/socialpyre/fastapi-hotwire/branches/main/protection --jq '{linear: .required_linear_history.enabled, signed: .required_signatures.enabled, force: .allow_force_pushes.enabled, delete: .allow_deletions.enabled}'
```

Both should return the configured values without error.
