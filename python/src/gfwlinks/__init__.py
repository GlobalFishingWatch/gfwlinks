"""Build shareable Global Fishing Watch map links from vessel ids.

- `vessel_profile_url` -- page for a single vessel.
- `vessel_map_url` -- map showing one or more vessels' tracks.
"""

import re
from urllib.parse import quote

__all__ = ["vessel_profile_url", "vessel_map_url"]

BASE = "https://globalfishingwatch.org/map"
PIPE_VERSION = "4"                     # frontend: PIPE_DATASET_VERSION (Vite build env)
_V = f"v{PIPE_VERSION}.0"
IDENTITY = f"public-global-vessel-identity:{_V}"
TRACKS = f"public-global-all-tracks:{_V}"
EVENTS = [f"public-global-{e}-events:{_V}" for e in
          ("fishing", "port-visits", "encounters", "loitering", "gaps")]
TRACK_DATAVIEW = f"fishing-map-vessel-track-v-{PIPE_VERSION}"
DEFAULT_EVENTS = ("fishing", "encounter", "port_visit", "gaps")
COLORS = ("#F95E5E", "#33B679", "#F09300", "#1AFF6B", "#F4511F", "#0B8043", "#069688",
          "#4184F4", "#AD1457", "#C0CA33", "#8E24A9", "#ABFF34", "#FCA26F")


def _fmt(v):
    if v is True or v is False:        # before the int check: bool IS an int
        return "true" if v else "false"
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return str(v)
    for d in range(18):                # shortest fixed-notation that round-trips; the R
        s = "%.*f" % (d, v)            # twin uses the same loop because R lacks a
        if float(s) == v:              # shortest-roundtrip primitive. See PLAN.md §9.
            return s
    raise ValueError(f"cannot format {v!r}")


def _query(pairs):
    pairs = sorted((k, _fmt(v)) for k, v in pairs if v is not None)   # URLSearchParams.sort()
    return "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in pairs)


def _viewport(latitude, longitude, zoom, start, end):
    return [("latitude", latitude), ("longitude", longitude), ("zoom", zoom),
            ("start", start), ("end", end)]


def vessel_profile_url(vessel_id, identity_source="selfReportedInfo",
                        visible_events=DEFAULT_EVENTS, latitude=None, longitude=None,
                        zoom=None, start=None, end=None):
    """URL for a single vessel's profile page.

    Args:
        vessel_id: Vessel id (the ``id`` field from the GFW API/vessel search).
        identity_source: Which identity record to show: ``"selfReportedInfo"``
            (default) or ``"registryInfo"``. Note the live app instead defaults
            to ``"registryInfo"`` with a fallback; see DEVELOPMENT.md.
        visible_events: Event layers to show, e.g. ``"fishing"``,
            ``"encounter"``, ``"port_visit"``, ``"loitering"``, ``"gaps"``.
            Defaults to all but ``"loitering"``.
        latitude: Viewport latitude. Optional; omit along with `longitude`
            and `zoom` for the map's default view.
        longitude: Viewport longitude.
        zoom: Viewport zoom level.
        start: ISO 8601 timestamp (e.g. ``"2026-01-01T00:00:00.000Z"``)
            bounding the start of the activity time range shown.
        end: ISO 8601 timestamp bounding the end of the activity time range.

    Returns:
        str: The vessel profile page URL.

    Example:
        >>> vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
        >>> vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501",
        ...                     latitude=-43.4, longitude=176.3, zoom=8.6)
    """
    if not re.fullmatch(r"[A-Za-z0-9:._-]+", vessel_id):   # lands in the PATH: a stray
        raise ValueError(f"suspicious vessel_id: {vessel_id!r}")   # ?/# changes the URL
    pairs = [("vDi", IDENTITY), ("vIs", identity_source), ("vSRi", vessel_id)]
    pairs += [(f"vE[{i}]", e) for i, e in enumerate(visible_events)]
    pairs += _viewport(latitude, longitude, zoom, start, end)
    return f"{BASE}/vessel/{vessel_id}?{_query(pairs)}"


def vessel_map_url(vessel_ids, latitude=None, longitude=None, zoom=None,
                    start=None, end=None):
    """URL for a map showing one or more vessels' tracks.

    Adds each vessel as its own dataview (distinct colour, identity, track
    and event layers), and hides the default background activity layers
    (``ais``, ``vms``) so the vessel tracks aren't buried under them.

    Args:
        vessel_ids: List of vessel ids to show together (not a single string).
        latitude: Viewport latitude. Optional; when omitted (along with
            `longitude` and `zoom`) the map opens at its default (world) view,
            since this function does not compute a fit-bounds around the
            vessels.
        longitude: Viewport longitude.
        zoom: Viewport zoom level.
        start: ISO 8601 timestamp (e.g. ``"2026-01-01T00:00:00.000Z"``)
            bounding the start of the activity time range shown.
        end: ISO 8601 timestamp bounding the end of the activity time range.

    Returns:
        str: A single URL showing all of `vessel_ids`.

    Raises:
        TypeError: If `vessel_ids` is a single string instead of a list.

    Example:
        >>> vessel_map_url(["91da818da-ab9b-1556-e335-ca41831da501",
        ...                 "41a98a2e0-0fbb-3d26-4b71-6d4266443a82"],
        ...                 latitude=-43.4, longitude=176.3, zoom=8.6)
    """
    if isinstance(vessel_ids, str):        # else iterates chars into one id per letter
        raise TypeError("vessel_ids must be a list of ids, not a single string")
    pairs = []
    for i, v in enumerate(vessel_ids):
        pairs += [(f"dvIn[{i}][id]", f"vessel-{v}:{_V}"),
                  (f"dvIn[{i}][dvId]", TRACK_DATAVIEW),
                  (f"dvIn[{i}][cfg][clr]", COLORS[i % len(COLORS)]),
                  (f"dvIn[{i}][cfg][info]", IDENTITY),
                  (f"dvIn[{i}][cfg][track]", TRACKS)]
        pairs += [(f"dvIn[{i}][cfg][events][{j}]", e) for j, e in enumerate(EVENTS)]
    # ais/vms are the only visible default-workspace layers; hide so tracks aren't buried
    for j, layer in enumerate(("ais", "vms"), start=len(vessel_ids)):
        pairs += [(f"dvIn[{j}][id]", layer), (f"dvIn[{j}][cfg][vis]", False)]
    pairs += [("tV", "vessel")] + _viewport(latitude, longitude, zoom, start, end)
    return f"{BASE}/fishing-activity/default-public?{_query(pairs)}"
