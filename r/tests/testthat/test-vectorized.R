r_dir <- testthat::test_path("..", "..", "R")
if (dir.exists(r_dir)) for (f in list.files(r_dir, "[.]R$", full.names = TRUE)) source(f)

test_that("vessel_profile_url is vectorized over vessel_id", {
  urls <- vessel_profile_url(c("abc", "def"), latitude = c(1, 2), longitude = c(3, 4), zoom = 5)
  expect_length(urls, 2)
  expect_true(all(grepl("^https://", urls)))
})

test_that("visible_events is passed whole to every call, not recycled", {
  urls <- vessel_profile_url(c("abc", "def"), visible_events = c("fishing", "gaps"))
  expect_true(all(grepl("vE%5B0%5D=fishing", urls)))
  expect_true(all(grepl("vE%5B1%5D=gaps", urls)))
})
