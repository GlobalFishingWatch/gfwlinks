# Development notes

This package re-implements URL-encoding logic copied from the GFW frontend
app (`GlobalFishingWatch/frontend`). If the frontend changes how it builds
these URLs, this package drifts out of sync and needs a matching update —
nothing here checks that automatically.

Python and R each expose the same two functions, driven by one shared spec
(`specs/url_test_cases.json`) so both stay provably identical to each other.
Zero runtime dependencies (stdlib / base R only).

## Testing

```bash
cd python && uv run pytest
cd r && Rscript -e 'testthat::test_dir("tests/testthat")'
```

Both suites check output against `specs/url_test_cases.json`.

## Ground truth

Verified against `frontend@develop` at commit
[`edcd7db`](https://github.com/GlobalFishingWatch/frontend/commit/edcd7db8d19be2f07d45dade976a5a7450110d16).
See that commit's `url-workspace.ts`, `dataviews.utils.ts`, `workspaces.ts`,
`vessel.config.ts`, `color-bar-options.ts`, and `events.ts` for the pieces
this copies (key abbreviations, sort order, dataview ids, colours, versions).

Two spec cases (`single_vessel_minimal`, `multiple_vessels_together`) were
additionally confirmed by loading the generated URL in the live map with
Playwright. The other three (`numeric_precision`, `single_item_list`,
`large_fleet`) are synthetic edge cases — see each case's `description` in
the spec file.

## Known divergences from the app

- `vessel_profile_url` defaults to `identity_source="selfReportedInfo"`; the
  app defaults to `registryInfo` with a fallback.
- Dataview colours always start at palette index `[0]`; the app assigns by
  pin order against already-used colours, so order can differ (same colours).
- No fit-bounds parameter — without an explicit viewport, `vessel_map_url`
  opens at the world default view.
- URLs are literal, not qs-tokenized — longer than the app's, never wrong;
  the app parses literal URLs the same way.

## Org policy

Per Global Fishing Watch AI policy: this analysis is the responsibility of
the reviewing analyst — check the sources above yourself, and note
`frontend@develop` moves, so a later commit may already differ. No vibe
coding to production: before relying on `_fmt` (`python/src/gfwlinks/__init__.py`)
or `.fmt`/`order(..., method = "radix")` (`r/R/gfwlinks.R`), understand why
they're written that way (see the code comments — `%g` formatting diverges
from JS on some values, and R's default `order()` is locale-dependent even
under `LC_COLLATE=C`).
