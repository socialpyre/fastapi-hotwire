# Flash messages example

Two ways to deliver flash messages with `fastapi-hotwire`: classic post-redirect-get, and a Hotwire-native turbo-stream that updates the flash region without a redirect.

## Run

```bash
cd examples/flash
uv run --with fastapi-hotwire --with uvicorn uvicorn app:app --reload
```

Then open http://127.0.0.1:8000.

## What it shows

- `flash(request, "...", category=...)` to queue a message in the session.
- `RedirectResponse("/")` then a fresh page render — `HotwireTemplates` automatically drains the queue into a `flashes` template variable.
- `flash.stream(request, "...", category=...)` to push the flash as a turbo-stream that appends to `#flash` without a navigation.
- A small Stimulus controller that auto-dismisses each flash after 5s, including across Turbo's bfcache.
