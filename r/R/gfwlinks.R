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
  o <- order(names(pairs), method = "radix")      # MANDATORY, see PLAN.md §9
  enc <- function(s) utils::URLencode(s, reserved = TRUE)
  paste(vapply(names(pairs)[o], enc, ""),
        vapply(vapply(pairs[o], .fmt, ""), enc, ""), sep = "=", collapse = "&")
}

.viewport <- function(latitude, longitude, zoom, start, end) {
  list(latitude = latitude, longitude = longitude, zoom = zoom, start = start, end = end)
}

vessel_profile_url <- function(vessel_id, identity_source = "selfReportedInfo",
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

vessel_tracks_url <- function(vessel_ids, latitude = NULL, longitude = NULL, zoom = NULL,
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
