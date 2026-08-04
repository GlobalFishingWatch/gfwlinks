# gfwlinks

Build Global Fishing Watch map URLs without needing the frontend monorepo's
encoder (`libs/skills/src/encode-url/`). Two sibling packages — Python and
R — each expose the same two functions, driven by one shared spec so both are
provably identical:

- `vessel_profile_url(vessel_id, ...)` — single vessel, route `/map/vessel/<id>`
- `vessel_tracks_url(vessel_ids, ...)` — N vessels, route `/map/fishing-activity/default-public`

Both packages have **zero runtime dependencies** (stdlib / base R only).

## Usage

Python:

```python
import gfwlinks
gfwlinks.vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
gfwlinks.vessel_tracks_url(["91da818da-...", "41a98a2e0-..."], latitude=-43.4, longitude=176.3, zoom=8.6)
```

R:

```r
source("R/gfwlinks.R")
vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
vessel_tracks_url(c("91da818da-...", "41a98a2e0-..."), latitude = -43.4, longitude = 176.3, zoom = 8.6)
```

## Testing

```
cd python && uv run pytest
cd r && Rscript -e 'testthat::test_dir("tests/testthat")'
```

Both suites read `specs/url_test_cases.json` and assert byte-identical output —
the cross-language proof. Two of the five cases were additionally verified by
loading the generated URL in the live map via Playwright (see below).

## Ground truth

Verified against `GlobalFishingWatch/frontend@develop` at commit
[`edcd7db`](https://github.com/GlobalFishingWatch/frontend/commit/edcd7db8d19be2f07d45dade976a5a7450110d16).

| What we copy | Source |
|---|---|
| abbreviated keys, stringify | `libs/dataviews-client/src/url-workspace/url-workspace.ts` |
| the alphabetical sort | `apps/fishing-map/router.tsx` → `params.sort()` |
| vessel instance builder | `apps/fishing-map/features/dataviews/dataviews.utils.ts` |
| vessel instance id format | `libs/dataviews-client/src/dataviews.utils.ts`, `src/config.ts` |
| profile params all optional | `apps/fishing-map/router/routes.search.ts` |
| track dataview slug | `apps/fishing-map/config/src/workspaces.ts` |
| version numbers | `libs/datasets-client/src/config.ts` |
| identity dataset id | `apps/fishing-map/features/vessel/vessel.config.ts` |
| colour cycle | `libs/ui-components/src/color-bar/color-bar-options.ts` |
| event types | `libs/api-types/src/events.ts` |

Two of five spec cases (`single_vessel_minimal`, `multiple_vessels_together`)
use real vessel ids and were confirmed by navigating the generated URL in the
live map with Playwright: the sidebar shows the correct vessel name/flag
("Venture K" / New Zealand, "F.V. Ocean Pioneer"), the right colours and date
range, and the console has no `DataviewInstance id: ... doesn't have a valid
dataview` warning (the silent-drop failure mode a self-consistent test suite
alone can't catch). The remaining three cases (`numeric_precision`,
`single_item_list`, `large_fleet`) are synthetic and exercise formatting edge
cases — see each case's `description` field in `specs/url_test_cases.json`
for what it targets.

## Known divergences from the app

- **Identity source default.** We default `vessel_profile_url` to
  `identity_source="selfReportedInfo"`; the app defaults to `registryInfo`
  with a fallback. Deliberate — predictable for AIS-only vessels — but means
  our profile URL isn't byte-identical to the app's for a registry vessel.
- **Colour assignment.** The app assigns dataview colours by pin order
  against already-used colours (`getNextColor`), so a captured two-vessel URL
  can show colours out of palette order (e.g. `[1]` then `[0]`). Our cycle
  always starts at `[0]`. Same colours, different order — cosmetic only.
- **No fit-bounds parameter exists.** `vessel_tracks_url` without an explicit
  viewport opens at the world default (`latitude:19, longitude:26, zoom:1.49`)
  with tracks possibly off-screen.
- **Literal values, not tokenized.** We emit literal URLs instead of qs's
  `~0`/`tk[]` reference compression. The app's `parseWorkspace` accepts and
  renders literal URLs identically (confirmed live — see above), so this only
  means our URLs are a bit longer, never wrong.

## Org policy

Per Global Fishing Watch AI policy: this analysis and its outputs are the
responsibility of the reviewing analyst — check the sources above yourself
before treating them as authoritative, and note that `frontend@develop` moves,
so a later commit may have changed something already. For the code: no vibe
coding to production — before relying on `_fmt` (`python/src/gfwlinks/__init__.py`)
or `.fmt`/`order(..., method = "radix")` (`r/R/gfwlinks.R`), understand why
they're written that way (documented in code comments and confirmed by hand:
`%g` formatting flips to exponential notation and diverges from JS; R's
default `order()` is locale-dependent — even under `LC_COLLATE=C`, since R
links ICU — and misorders bracketed array indices).
