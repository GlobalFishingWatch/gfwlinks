# gfwlinks

**Experimental, pre-1.0** — API may change without notice.

Build shareable Global Fishing Watch map links from vessel ids — no need to open the map and click through the UI.

Available for Python and R, with the same two functions in both:

- `vessel_profile_url(vessel_id, ...)` — page for a single vessel
- `vessel_map_url(vessel_ids, ...)` — map showing one or more vessels' tracks

## Install

Python:

```bash
pip install "git+https://github.com/GlobalFishingWatch/gfwlinks.git@v0.1.0#subdirectory=python"
```

R:

```r
remotes::install_github("GlobalFishingWatch/gfwlinks", subdir = "r", ref = "v0.1.0")
```

## Usage

`vessel_id` is the vessel's `id` field as returned by the [GFW API](https://globalfishingwatch.org/our-apis/documentation#dataset-comparison-overview) or vessel search. See the [gfwr identity guide](https://globalfishingwatch.github.io/gfwr/articles/identity#vesselid) for how vessel identity works across GFW's datasets.

Python:

```python
import gfwlinks

# Link to a single vessel's profile page, centered on a place and time range
gfwlinks.vessel_profile_url(
    "91da818da-ab9b-1556-e335-ca41831da501",
    latitude=-41.0, longitude=174.5, zoom=5,
    start="2026-01-01T00:00:00.000Z", end="2026-01-31T00:00:00.000Z",
)

# Link to the map showing multiple vessels' tracks together
gfwlinks.vessel_map_url(
    ["91da818da-ab9b-1556-e335-ca41831da501", "41a98a2e0-0fbb-3d26-4b71-6d4266443a82"],
    latitude=-43.4, longitude=176.3, zoom=8.6,
    start="2026-07-02T00:00:00.000Z", end="2026-07-31T00:00:00.000Z",
)
```

R:

```r
library(gfwlinks)

# Link to a single vessel's profile page, centered on a place and time range
vessel_profile_url(
    "91da818da-ab9b-1556-e335-ca41831da501",
    latitude = -41.0, longitude = 174.5, zoom = 5,
    start = "2026-01-01T00:00:00.000Z", end = "2026-01-31T00:00:00.000Z"
)

# Link to the map showing multiple vessels' tracks together
vessel_map_url(
    c("91da818da-ab9b-1556-e335-ca41831da501", "41a98a2e0-0fbb-3d26-4b71-6d4266443a82"),
    latitude = -43.4, longitude = 176.3, zoom = 8.6,
    start = "2026-07-02T00:00:00.000Z", end = "2026-07-31T00:00:00.000Z"
)
```

`latitude`, `longitude`, `zoom`, `start`, and `end` are optional — pass them to open the map centered on a specific place and time range instead of the default view.

## Learn more

For how this is implemented, tested, and verified against the live map, plus known differences from what the app itself produces, see
[DEVELOPMENT.md](DEVELOPMENT.md).
