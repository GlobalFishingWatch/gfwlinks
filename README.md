# gfwlinks

**Experimental, pre-1.0** — API may change without notice.

Build shareable Global Fishing Watch map links from vessel ids — no need to open the map and click through the UI.

Available for Python and R, with the same two functions in both:

- `vessel_profile_url(vessel_id, ...)` — page for a single vessel
- `vessel_map_url(vessel_ids, ...)` — map showing one or more vessels' tracks

## Install

Python:

```bash
pip install "git+https://github.com/GlobalFishingWatch/gfwlinks.git#subdirectory=python"
```

R:

```r
remotes::install_github("GlobalFishingWatch/gfwlinks", subdir = "r")
```

## Usage

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
