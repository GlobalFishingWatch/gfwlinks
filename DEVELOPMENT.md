# Development notes

This package re-implements URL-encoding logic copied from the GFW frontend app (`GlobalFishingWatch/frontend`). If the frontend changes how it builds these URLs, this package drifts out of sync and needs a matching update — nothing here checks that automatically.

Python and R each expose the same two functions, driven by one shared spec (`specs/url_test_cases.json`) so both stay provably identical to each other. Zero runtime dependencies (stdlib / base R only).

## Testing

```bash
cd python && uv run pytest
cd r && Rscript -e 'testthat::test_dir("tests/testthat")'
```

Both suites check output against `specs/url_test_cases.json`. CI
(`.github/workflows/test.yml`) runs both on every PR.

### Live app check

The suites above only prove the two implementations agree with each other and with a frozen string. They cannot notice changes in frontend code. `python/tests/test_live.py` closes that gap by loading each spec URL in a real browser and asserting the app still asks its own API for what the URL specified:

```bash
cd python
uv run --group live playwright install chromium     # once
GFWLINKS_LIVE=1 uv run --group live pytest tests/test_live.py
```

It is opt-in (skipped without `GFWLINKS_LIVE`) and runs regularly via `.github/workflows/live.yml`. Note a failure can equally mean the app is down, and that shouldn't block an unrelated merge. Only cases flagged `"live": true` in the spec are checked.

Asserted, per vessel in the URL: an identity call and a track call, each naming the dataset the URL specified, plus at least one event call. `vessel_map_url` links additionally assert every event dataset they declare; `vessel_profile_url` links only assert that some event call fires, since which event types get requested depends on `visible_events` and the API's own dataset names don't map 1:1 to it. All calls return 2xx, and our vessel ids survive the app's own query-string rewrite. Screenshots land in `python/live-screenshots/` (uploaded as a CI artifact) for a human to eyeball.

Deliberately not asserted: the API's `start-date`/`end-date` (the app widens our range to whole-year buckets and filters client-side -- the visible date range is checkable on the screenshot's timebar instead), and `gaps` events, which the app never requests for a vessel even when the URL asks for one -- a real gap in coverage, not a check we're skipping for convenience.

`test_canary_catches_a_broken_url` in the same file proves this check can actually fail: it feeds a URL with a mangled dataset version through and asserts the assertions above catch it.

## Versioning

Semantic versioning (`MAJOR.MINOR.PATCH`). Python (`python/pyproject.toml`) and R (`r/DESCRIPTION`) each track their own version string — nothing enforces they match, so bump both together on release. Pre-1.0: anything may break between minor versions.

## Ground truth

Verified against `frontend@develop` at commit [`edcd7db`](https://github.com/GlobalFishingWatch/frontend/commit/edcd7db8d19be2f07d45dade976a5a7450110d16). See that commit's `url-workspace.ts`, `dataviews.utils.ts`, `workspaces.ts`, `vessel.config.ts`, `color-bar-options.ts`, and `events.ts` for the pieces this copies (key abbreviations, sort order, dataview ids, colours, versions).

Two spec cases (`single_vessel_minimal`, `multiple_vessels_together`) were additionally confirmed by loading the generated URL in the live map with Playwright. The other three (`numeric_precision`, `single_item_list`, `large_fleet`) are synthetic edge cases — see each case's `description` in the spec file. Four of the five are now re-confirmed automatically every week; see "Live app check" above.

## Known divergences from the app

- `vessel_profile_url` defaults to `identity_source="selfReportedInfo"`, since nearly every vessel has one; the app defaults to `registryInfo` instead.
- Dataview colours always start at palette index `[0]`; the app assigns by pin order against already-used colours, so order can differ (same colours).
- No fit-bounds parameter — without an explicit viewport, `vessel_map_url` opens at the world default view.
- URLs are literal, not qs-tokenized — longer than the app's, never wrong; the app parses literal URLs the same way.
