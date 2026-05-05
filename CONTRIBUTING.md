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
