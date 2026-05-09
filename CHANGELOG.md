# CHANGELOG

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/) and uses [Conventional Commits](https://www.conventionalcommits.org/) so that releases — version bump, changelog entry, GitHub Release, and PyPI publish — are produced automatically by [`python-semantic-release`](https://python-semantic-release.readthedocs.io/) on every push to `main`.

<!-- version list -->

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
