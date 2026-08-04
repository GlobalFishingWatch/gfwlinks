#' gfwlinks: Build Global Fishing Watch Map URLs
#'
#' Build shareable Global Fishing Watch map links from vessel ids, without
#' opening the map and clicking through the UI. See [vessel_profile_url()]
#' and [vessel_map_url()].
#'
#' @keywords internal
"_PACKAGE"

# DEFAULT_EVENTS is a real top-level binding, but Vectorize() rewrites the
# function that references it as a default arg, so codetools can't see the
# reference and flags a false-positive "no visible binding" NOTE.
utils::globalVariables("DEFAULT_EVENTS")
