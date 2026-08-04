# uvr cannot install a package-under-development (uvr#188), so load sources directly.
# Under R CMD check the package is attached and R/ is absent, so this is a no-op.
r_dir <- testthat::test_path("..", "..", "R")
if (dir.exists(r_dir)) for (f in list.files(r_dir, "[.]R$", full.names = TRUE)) source(f)

test_that("urls match the shared spec", {
  spec_path <- testthat::test_path("..", "..", "..", "specs", "url_test_cases.json")
  skip_if_not(file.exists(spec_path), "spec not reachable (R CMD check)")
  # simplifyVector = FALSE keeps JSON arrays as lists so one-element arrays don't
  # collapse to scalars and diverge from Python (see PLAN.md §9)
  spec <- jsonlite::fromJSON(spec_path, simplifyVector = FALSE)
  for (case in spec$cases)
    expect_identical(do.call(get(case[["function"]]), case$args), case$url,
                     info = case$name)
})
