## Summary

<!-- One or two sentences on what this changes and why. -->

## Linked issue

<!-- Closes #N, or "no issue — typo / docs only". -->

## Type

- [ ] `feat:` new public API or behavior
- [ ] `fix:` bug fix
- [ ] `docs:` README / docstrings / examples
- [ ] `chore:` tooling / refactor with no behavior change
- [ ] `ci:` CI / build / release plumbing
- [ ] `test:` tests only

## Checklist

- [ ] Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/) (the pre-commit hook validates this).
- [ ] `uv run pytest` passes locally.
- [ ] `uvx ruff check . && uvx ruff format --check . && uvx ty check .` are clean.
- [ ] If this is a `feat:` / `fix:`, there's a test that covers the new behavior or regression.
- [ ] Public-API additions are exported from `fastapi_hotwire/__init__.py` and listed in the README's "What's in the box" table.
- [ ] No new dependencies were added without a note in the PR body explaining why.

## Notes for reviewers

<!-- Anything non-obvious about the implementation, edge cases worth a second look, alternatives considered. -->
