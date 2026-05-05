# Security policy

`fastapi-hotwire` is shared under the MIT license. There is no commercial support, no SLA, and no warranty — see [LICENSE](LICENSE). With that in mind, security findings are still welcome, since users of the package benefit when they're addressed.

## Reporting a finding

Please report findings **privately**, not in public issues:

- Open a private advisory via GitHub's [Report a vulnerability](https://github.com/socialpyre/fastapi-hotwire/security/advisories/new) form.

Helpful information to include:

- A description of the issue and its impact.
- Steps to reproduce, ideally a minimal FastAPI app or test case.
- Affected version(s) of `fastapi-hotwire` and Python.
- Whether the finding is already public somewhere.

Reports will be reviewed when bandwidth allows. There is no committed turnaround time — this project is shared as-is. Findings that affect the latest released version are most likely to get attention.

## Supported versions

Only the **latest released version** is supported. Older versions will not receive backport fixes.

## Areas of particular interest

The package ships a few primitives where security expectations are explicit and bugs are most consequential:

- **`fastapi_hotwire.streams`** — the trust contract for the `html` argument (raw, un-escaped) and the attribute-escaping path for `target` / `targets` / `request_id`.
- **`fastapi_hotwire.forms`** — the HMAC time-trap form token (`make_form_token` / `verify_form_token`). Sized for an anti-bot tripwire, **not** as a CSRF token or session token.
- **`fastapi_hotwire.csrf`** — the `Origin` / `Referer` validator and per-DNS-label wildcard semantics.
- **`fastapi_hotwire.templates.HotwireTemplates`** — the autoescape assertion at construction time.
- **`fastapi_hotwire.flash`** — flash content rides in a signed-but-not-encrypted session cookie; the doc strings call out what is and isn't safe to put there.

If you find a way to bypass any of those guarantees, that's exactly the kind of report that's most useful.

## What's out of scope

- Issues in dependencies (`fastapi`, `jinja2`, `pydantic`, etc.) — please report those upstream.
- Generic CSRF / clickjacking / XSS guidance that applies to any web framework — those are documented patterns the user is expected to apply.
- Configuration mistakes in user code (e.g. passing un-escaped user input to `streams.append(...)`) — that's the documented trust contract working as designed.
