"""Build shareable Global Fishing Watch map links from vessel ids.

- `vessel_profile_url` -- page for a single vessel.
- `vessel_map_url` -- map showing one or more vessels' tracks.
"""

import re
from urllib.parse import quote

__all__ = ["vessel_profile_url", "vessel_map_url"]

MAP_BASE_URL = "https://globalfishingwatch.org/map"
PIPE_VERSION = "4"                     # frontend: PIPE_DATASET_VERSION (Vite build env)
DATASET_VERSION = f"v{PIPE_VERSION}.0"
IDENTITY_DATASET = f"public-global-vessel-identity:{DATASET_VERSION}"
TRACKS_DATASET = f"public-global-all-tracks:{DATASET_VERSION}"
EVENT_DATASETS = [f"public-global-{event}-events:{DATASET_VERSION}" for event in
                  ("fishing", "port-visits", "encounters", "loitering", "gaps")]
TRACK_DATAVIEW_ID = f"fishing-map-vessel-track-v-{PIPE_VERSION}"
DEFAULT_EVENTS = ("fishing", "encounter", "port_visit", "gaps")
TRACK_COLORS = ("#F95E5E", "#33B679", "#F09300", "#1AFF6B", "#F4511F", "#0B8043", "#069688",
                "#4184F4", "#AD1457", "#C0CA33", "#8E24A9", "#ABFF34", "#FCA26F")

# The query-string keys below are the frontend's own abbreviations (see
# DEVELOPMENT.md "Ground truth") -- they are wire format, not ours to rename:
#   vDi   vessel dataset id          dvIn        dataview instances (array)
#   vIs   vessel identity source     dvIn[][dvId]  dataview id it instantiates
#   vSRi  vessel self-reported id    dvIn[][cfg]   dataview config
#   vE    visible events (array)     cfg[clr]      track colour
#   tV    timebar visualisation      cfg[vis]      layer visible?


def _format_value(value):
    if value is True or value is False:    # before the int check: bool IS an int
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    for decimals in range(18):             # shortest fixed-notation that round-trips; the R
        text = "%.*f" % (decimals, value)  # twin uses the same loop because R lacks a
        if float(text) == value:           # shortest-roundtrip primitive like JS's String(n)
            return text
    raise ValueError(f"cannot format {value!r}")


def _encode_query(params):
    params = sorted((key, _format_value(value))                       # URLSearchParams.sort()
                    for key, value in params if value is not None)
    return "&".join(f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in params)


def _viewport_params(latitude, longitude, zoom, start, end):
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

    Raises:
        TypeError: If `visible_events` is a single string instead of a list.

    Example:
        >>> vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
        >>> vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501",
        ...                     latitude=-43.4, longitude=176.3, zoom=8.6)
    """
    if not re.fullmatch(r"[A-Za-z0-9:._-]+", vessel_id):   # lands in the PATH: a stray
        raise ValueError(f"suspicious vessel_id: {vessel_id!r}")   # ?/# changes the URL
    if isinstance(visible_events, str):    # else iterates chars into one event per letter
        raise TypeError("visible_events must be a list of events, not a single string")
    params = [("vDi", IDENTITY_DATASET), ("vIs", identity_source), ("vSRi", vessel_id)]
    params += [(f"vE[{i}]", event) for i, event in enumerate(visible_events)]
    params += _viewport_params(latitude, longitude, zoom, start, end)
    return f"{MAP_BASE_URL}/vessel/{vessel_id}?{_encode_query(params)}"


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
    params = []
    for vessel_index, vessel_id in enumerate(vessel_ids):
        dataview = f"dvIn[{vessel_index}]"
        params += [(f"{dataview}[id]", f"vessel-{vessel_id}:{DATASET_VERSION}"),
                   (f"{dataview}[dvId]", TRACK_DATAVIEW_ID),
                   (f"{dataview}[cfg][clr]", TRACK_COLORS[vessel_index % len(TRACK_COLORS)]),
                   (f"{dataview}[cfg][info]", IDENTITY_DATASET),
                   (f"{dataview}[cfg][track]", TRACKS_DATASET)]
        params += [(f"{dataview}[cfg][events][{event_index}]", event_dataset)
                   for event_index, event_dataset in enumerate(EVENT_DATASETS)]
    # ais/vms are the only visible default-workspace layers; hide so tracks aren't buried
    for layer_index, layer in enumerate(("ais", "vms"), start=len(vessel_ids)):
        dataview = f"dvIn[{layer_index}]"
        params += [(f"{dataview}[id]", layer), (f"{dataview}[cfg][vis]", False)]
    params += [("tV", "vessel")] + _viewport_params(latitude, longitude, zoom, start, end)
    return f"{MAP_BASE_URL}/fishing-activity/default-public?{_encode_query(params)}"
