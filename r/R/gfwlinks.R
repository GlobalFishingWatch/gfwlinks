BASE <- "https://globalfishingwatch.org/map"
PIPE_VERSION <- "4" # frontend: PIPE_DATASET_VERSION (Vite build env)
.V <- paste0("v", PIPE_VERSION, ".0")
IDENTITY <- paste0("public-global-vessel-identity:", .V)
TRACKS <- paste0("public-global-all-tracks:", .V)
EVENTS <- paste0("public-global-", c("fishing", "port-visits", "encounters", "loitering", "gaps"),
                  "-events:", .V)
TRACK_DATAVIEW <- paste0("fishing-map-vessel-track-v-", PIPE_VERSION)
DEFAULT_EVENTS <- c("fishing", "encounter", "port_visit", "gaps")
COLORS <- c("#F95E5E", "#33B679", "#F09300", "#1AFF6B", "#F4511F", "#0B8043", "#069688",
            "#4184F4", "#AD1457", "#C0CA33", "#8E24A9", "#ABFF34", "#FCA26F")

.fmt <- function(v) {
  if (is.logical(v)) return(if (v) "true" else "false")
  if (is.character(v)) return(v)
  for (d in 0:17) { s <- sprintf("%.*f", d, v); if (as.numeric(s) == v) return(s) }
  stop("cannot format number: ", v)
}

.query <- function(pairs) {
  pairs <- pairs[!vapply(pairs, is.null, logical(1))]
  # radix: locale-independent byte order, matching JS URLSearchParams.sort()
  o <- order(names(pairs), method = "radix")
  enc <- function(s) utils::URLencode(s, reserved = TRUE, repeated = TRUE)
  paste(vapply(names(pairs)[o], enc, ""),
        vapply(vapply(pairs[o], .fmt, ""), enc, ""), sep = "=", collapse = "&")
}

.viewport <- function(latitude, longitude, zoom, start, end) {
  list(latitude = latitude, longitude = longitude, zoom = zoom, start = start, end = end)
}

.vessel_profile_url_one <- function(vessel_id, identity_source = "selfReportedInfo",
                                     visible_events = DEFAULT_EVENTS, latitude = NULL,
                                     longitude = NULL, zoom = NULL, start = NULL, end = NULL) {
  if (!grepl("^[A-Za-z0-9:._-]+$", vessel_id)) {  # lands in the PATH: a stray ?/#
    stop("suspicious vessel_id: ", vessel_id)      # changes the URL
  }
  pairs <- list(vDi = IDENTITY, vIs = identity_source, vSRi = vessel_id)
  for (i in seq_along(visible_events)) {
    pairs[[sprintf("vE[%d]", i - 1)]] <- visible_events[[i]]
  }
  pairs <- c(pairs, .viewport(latitude, longitude, zoom, start, end))
  sprintf("%s/vessel/%s?%s", BASE, vessel_id, .query(pairs))
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
vessel_profile_url <- Vectorize(.vessel_profile_url_one,
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
  pairs <- list()
  for (i in seq_along(vessel_ids)) {
    idx <- i - 1
    v <- vessel_ids[[i]]
    pairs[[sprintf("dvIn[%d][id]", idx)]] <- paste0("vessel-", v, ":", .V)
    pairs[[sprintf("dvIn[%d][dvId]", idx)]] <- TRACK_DATAVIEW
    pairs[[sprintf("dvIn[%d][cfg][clr]", idx)]] <- COLORS[(idx %% length(COLORS)) + 1]
    pairs[[sprintf("dvIn[%d][cfg][info]", idx)]] <- IDENTITY
    pairs[[sprintf("dvIn[%d][cfg][track]", idx)]] <- TRACKS
    for (j in seq_along(EVENTS)) {
      pairs[[sprintf("dvIn[%d][cfg][events][%d]", idx, j - 1)]] <- EVENTS[[j]]
    }
  }
  # ais/vms are the only visible default-workspace layers; hide so tracks aren't buried
  layers <- c("ais", "vms")
  for (j in seq_along(layers)) {
    idx <- length(vessel_ids) + j - 1
    pairs[[sprintf("dvIn[%d][id]", idx)]] <- layers[[j]]
    pairs[[sprintf("dvIn[%d][cfg][vis]", idx)]] <- FALSE
  }
  pairs[["tV"]] <- "vessel"
  pairs <- c(pairs, .viewport(latitude, longitude, zoom, start, end))
  sprintf("%s/fishing-activity/default-public?%s", BASE, .query(pairs))
}
