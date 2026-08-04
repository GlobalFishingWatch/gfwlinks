import re
from urllib.parse import quote

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
    if not re.fullmatch(r"[A-Za-z0-9:._-]+", vessel_id):   # lands in the PATH: a stray
        raise ValueError(f"suspicious vessel_id: {vessel_id!r}")   # ?/# changes the URL
    pairs = [("vDi", IDENTITY), ("vIs", identity_source), ("vSRi", vessel_id)]
    pairs += [(f"vE[{i}]", e) for i, e in enumerate(visible_events)]
    pairs += _viewport(latitude, longitude, zoom, start, end)
    return f"{BASE}/vessel/{vessel_id}?{_query(pairs)}"


def vessel_tracks_url(vessel_ids, latitude=None, longitude=None, zoom=None,
                       start=None, end=None):
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
