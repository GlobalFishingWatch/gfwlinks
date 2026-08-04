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

## Versioning

Semantic versioning (`MAJOR.MINOR.PATCH`). Python (`python/pyproject.toml`)
and R (`r/DESCRIPTION`) each track their own version string — nothing
enforces they match, so bump both together on release. Pre-1.0: anything may
break between minor versions.

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
