MAP_BASE_URL <- "https://globalfishingwatch.org/map"
PIPE_VERSION <- "4" # frontend: PIPE_DATASET_VERSION (Vite build env)
DATASET_VERSION <- paste0("v", PIPE_VERSION, ".0")
IDENTITY_DATASET <- paste0("public-global-vessel-identity:", DATASET_VERSION)
TRACKS_DATASET <- paste0("public-global-all-tracks:", DATASET_VERSION)
EVENT_DATASETS <- paste0("public-global-",
                          c("fishing", "port-visits", "encounters", "loitering", "gaps"),
                          "-events:", DATASET_VERSION)
TRACK_DATAVIEW_ID <- paste0("fishing-map-vessel-track-v-", PIPE_VERSION)
DEFAULT_EVENTS <- c("fishing", "encounter", "port_visit", "gaps")
TRACK_COLORS <- c("#F95E5E", "#33B679", "#F09300", "#1AFF6B", "#F4511F", "#0B8043", "#069688",
                  "#4184F4", "#AD1457", "#C0CA33", "#8E24A9", "#ABFF34", "#FCA26F")

# The query-string keys below are the frontend's own abbreviations (see
# DEVELOPMENT.md "Ground truth") -- they are wire format, not ours to rename:
#   vDi   vessel dataset id          dvIn          dataview instances (array)
#   vIs   vessel identity source     dvIn[][dvId]  dataview id it instantiates
#   vSRi  vessel self-reported id    dvIn[][cfg]   dataview config
#   vE    visible events (array)     cfg[clr]      track colour
#   tV    timebar visualisation      cfg[vis]      layer visible?

.format_value <- function(value) {
  if (is.logical(value)) return(if (value) "true" else "false")
  if (is.character(value)) return(value)
  # shortest fixed-notation that round-trips; base R has no shortest-roundtrip
  # primitive like JS's String(n), so the Python twin uses the same loop
  for (decimals in 0:17) {
    text <- sprintf("%.*f", decimals, value)
    if (as.numeric(text) == value) return(text)
  }
  stop("cannot format number: ", value)
}

.encode_query <- function(params) {
  params <- params[!vapply(params, is.null, logical(1))]
  # radix: locale-independent byte order, matching JS URLSearchParams.sort()
  sorted <- order(names(params), method = "radix")
  percent_encode <- function(text) utils::URLencode(text, reserved = TRUE, repeated = TRUE)
  paste(vapply(names(params)[sorted], percent_encode, ""),
        vapply(vapply(params[sorted], .format_value, ""), percent_encode, ""),
        sep = "=", collapse = "&")
}

.viewport_params <- function(latitude, longitude, zoom, start, end) {
  list(latitude = latitude, longitude = longitude, zoom = zoom, start = start, end = end)
}

.vessel_profile_url_single <- function(vessel_id, identity_source = "selfReportedInfo",
                                        visible_events = DEFAULT_EVENTS, latitude = NULL,
                                        longitude = NULL, zoom = NULL, start = NULL, end = NULL) {
  if (!grepl("^[A-Za-z0-9:._-]+$", vessel_id)) {  # lands in the PATH: a stray ?/#
    stop("suspicious vessel_id: ", vessel_id)      # changes the URL
  }
  params <- list(vDi = IDENTITY_DATASET, vIs = identity_source, vSRi = vessel_id)
  for (event_index in seq_along(visible_events)) {
    params[[sprintf("vE[%d]", event_index - 1)]] <- visible_events[[event_index]]
  }
  params <- c(params, .viewport_params(latitude, longitude, zoom, start, end))
  sprintf("%s/vessel/%s?%s", MAP_BASE_URL, vessel_id, .encode_query(params))
}

#' URL for a single vessel's profile page
#'
#' Builds the URL for the GFW map page showing one vessel's identity,
#' activity and (optionally) a viewport centered on a place and time.
#'
#' Vectorized over every argument (via [base::Vectorize()]), so it can be
#' called with a column of vessel ids, e.g. `mutate(url = vessel_profile_url(vessel_id))`.
#' `visible_events` is the exception: it is passed whole to every call, not
#' recycled element-by-element, since it's a set of event types rather than
#' a per-vessel value.
#'
#' @param vessel_id Vessel id (the `id` field from the GFW API/vessel search).
#' @param identity_source Which identity record to show: `"selfReportedInfo"`
#'   (default) or `"registryInfo"`. Note the live app instead defaults to
#'   `"registryInfo"` with a fallback; see DEVELOPMENT.md.
#' @param visible_events Character vector of event layers to show, e.g.
#'   `"fishing"`, `"encounter"`, `"port_visit"`, `"loitering"`, `"gaps"`.
#'   Defaults to all but `"loitering"`.
#' @param latitude,longitude,zoom Map viewport. All three are optional; when
#'   omitted the map opens at its default view instead of a specific place.
#' @param start,end ISO 8601 timestamps (e.g. `"2026-01-01T00:00:00.000Z"`)
#'   bounding the activity time range shown.
#'
#' @return A character vector of URLs, one per `vessel_id`.
#' @export
#'
#' @examples
#' vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501")
#' vessel_profile_url("91da818da-ab9b-1556-e335-ca41831da501",
#'                     latitude = -43.4, longitude = 176.3, zoom = 8.6)
# vectorized so mutate(url = vessel_profile_url(vessel_id)) works over a column;
# visible_events stays whole per call (same events for every row), not zipped
vessel_profile_url <- Vectorize(.vessel_profile_url_single,
                                 vectorize.args = c("vessel_id", "identity_source",
                                                     "latitude", "longitude", "zoom",
                                                     "start", "end"),
                                 SIMPLIFY = TRUE, USE.NAMES = FALSE)

#' URL for a map showing one or more vessels' tracks
#'
#' Builds the URL for the GFW fishing-activity map with each vessel added as
#' its own dataview (distinct colour, identity, track and event layers), and
#' the default background activity layers (`ais`, `vms`) hidden so the
#' vessel tracks aren't buried under them.
#'
#' @param vessel_ids Character vector of vessel ids to show together.
#' @param latitude,longitude,zoom Map viewport. All three are optional; when
#'   omitted the map opens at its default (world) view, since this function
#'   does not compute a fit-bounds around the vessels.
#' @param start,end ISO 8601 timestamps (e.g. `"2026-01-01T00:00:00.000Z"`)
#'   bounding the activity time range shown.
#'
#' @return A single URL (character scalar) showing all of `vessel_ids`.
#' @export
#'
#' @examples
#' vessel_map_url(c("91da818da-ab9b-1556-e335-ca41831da501",
#'                   "41a98a2e0-0fbb-3d26-4b71-6d4266443a82"),
#'                 latitude = -43.4, longitude = 176.3, zoom = 8.6)
vessel_map_url <- function(vessel_ids, latitude = NULL, longitude = NULL, zoom = NULL,
                            start = NULL, end = NULL) {
  params <- list()
  for (i in seq_along(vessel_ids)) {
    vessel_index <- i - 1 # url arrays are 0-based
    vessel_id <- vessel_ids[[i]]
    params[[sprintf("dvIn[%d][id]", vessel_index)]] <-
      paste0("vessel-", vessel_id, ":", DATASET_VERSION)
    params[[sprintf("dvIn[%d][dvId]", vessel_index)]] <- TRACK_DATAVIEW_ID
    params[[sprintf("dvIn[%d][cfg][clr]", vessel_index)]] <-
      TRACK_COLORS[(vessel_index %% length(TRACK_COLORS)) + 1]
    params[[sprintf("dvIn[%d][cfg][info]", vessel_index)]] <- IDENTITY_DATASET
    params[[sprintf("dvIn[%d][cfg][track]", vessel_index)]] <- TRACKS_DATASET
    for (j in seq_along(EVENT_DATASETS)) {
      params[[sprintf("dvIn[%d][cfg][events][%d]", vessel_index, j - 1)]] <- EVENT_DATASETS[[j]]
    }
  }
  # ais/vms are the only visible default-workspace layers; hide so tracks aren't buried
  hidden_layers <- c("ais", "vms")
  for (j in seq_along(hidden_layers)) {
    layer_index <- length(vessel_ids) + j - 1
    params[[sprintf("dvIn[%d][id]", layer_index)]] <- hidden_layers[[j]]
    params[[sprintf("dvIn[%d][cfg][vis]", layer_index)]] <- FALSE
  }
  params[["tV"]] <- "vessel"
  params <- c(params, .viewport_params(latitude, longitude, zoom, start, end))
  sprintf("%s/fishing-activity/default-public?%s", MAP_BASE_URL, .encode_query(params))
}
