# CHANGELOG

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/) and uses [Conventional Commits](https://www.conventionalcommits.org/) so that releases — version bump, changelog entry, GitHub Release, and PyPI publish — are produced automatically by [`python-semantic-release`](https://python-semantic-release.readthedocs.io/) on every push to `main`.

<!-- version list -->

## v0.3.0 (2026-05-15)

### Chores

- Sync uv.lock to v0.2.0 + normalize specifiers
  ([`598b34d`](https://github.com/socialpyre/fastapi-hotwire/commit/598b34d309f40dceb020279f8ff8c4b0a1e19938))

### Continuous Integration

- Backport postpit's release-gate + tooling baseline
  ([`4239e50`](https://github.com/socialpyre/fastapi-hotwire/commit/4239e502ccdc2848150caada2863f272e2709834))

- Empty commit to retrigger workflow
  ([`19d565a`](https://github.com/socialpyre/fastapi-hotwire/commit/19d565a05c0e7c8704edd9caf561af61fd17165d))

- Lowercase workflow name in dependency-review.yml
  ([`dc7d69f`](https://github.com/socialpyre/fastapi-hotwire/commit/dc7d69fa028afda04afd1e55b651d241bff7c1df))

- Lowercase workflow names for consistency
  ([`738819d`](https://github.com/socialpyre/fastapi-hotwire/commit/738819d61297ae27c0a55ea6912835da4df9ae11))

### Features

- Drop csrf module
  ([`477df8b`](https://github.com/socialpyre/fastapi-hotwire/commit/477df8b6d901a180d85565913ace4bc71ec5bdc1))

### Breaking Changes

- `fastapi_hotwire.csrf` and `csrf.allowed_origin` are removed. Replace with `fastapi-csrf-protect`,
  `asgi-csrf`, or a small in-app Origin/Referer check. The removed module was ~50 LOC; see the prior
  commit on the v0.2.0 tag for a starting point if you want to copy it.


## v0.2.0 (2026-05-09)

### Documentation

- Rebrand LICENSE and package author to Pyre
  ([`6423e2b`](https://github.com/socialpyre/fastapi-hotwire/commit/6423e2ba2be6c13c26103bd7737112127a9ee43e))

- Recast SECURITY and CoC for as-is sharing without personal contact
  ([`1b7b876`](https://github.com/socialpyre/fastapi-hotwire/commit/1b7b87603987e33a96a85cd05fb765ff8cb2b002))

- **contributing**: Add repo configuration runbook for maintainers
  ([`1431a3d`](https://github.com/socialpyre/fastapi-hotwire/commit/1431a3d42d34c68dab4c690beb2bd6c2219917a3))

- **contributing**: Drop signed-commits requirement (semantic-release bot can't sign)
  ([`6ad3a9b`](https://github.com/socialpyre/fastapi-hotwire/commit/6ad3a9b5dadc16dc3789255b1b794003f353a1e7))

- **readme**: Rewrite intro and refresh badge URLs
  ([`653f869`](https://github.com/socialpyre/fastapi-hotwire/commit/653f86990c5dd2f85254c8a4a879228a9c202e9f))

### Features

- Remove form-token / time-trap helpers
  ([`b3b1222`](https://github.com/socialpyre/fastapi-hotwire/commit/b3b1222163e263915eee3b4155bd7f662a5721a6))

### Breaking Changes

- Make_form_token and verify_form_token are removed. Use a dedicated CSRF / anti-bot solution
  instead.


## v0.1.0 (2026-05-05)

- Initial Release
