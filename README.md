# gfwlinks

Build shareable Global Fishing Watch map links from vessel ids — no need to
open the map and click through the UI.

Available for Python and R, with the same two functions in both:

- `vessel_profile_url(vessel_id, ...)` — page for a single vessel
- `vessel_tracks_url(vessel_ids, ...)` — map showing one or more vessels' tracks

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
gfwlinks.vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
gfwlinks.vessel_tracks_url(["91da818da-...", "41a98a2e0-..."], latitude=-43.4, longitude=176.3, zoom=8.6)
```

R:

```r
library(gfwlinks)
vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
vessel_tracks_url(c("91da818da-...", "41a98a2e0-..."), latitude = -43.4, longitude = 176.3, zoom = 8.6)
```

`latitude`, `longitude`, `zoom`, `start`, and `end` are optional — pass them
to open the map centered on a specific place and time range instead of the
default view.

## Learn more

For how this is implemented, tested, and verified against the live map, plus
known differences from what the app itself produces, see
[DEVELOPMENT.md](DEVELOPMENT.md).
