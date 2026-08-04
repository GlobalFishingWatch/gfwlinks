"""Live check: load each spec URL in a real browser and assert the app still
understands our parameters.

test_spec.py only proves the two implementations agree with a frozen string;
it can't tell if the frontend renamed a param or bumped a dataset version.
This drives the live app and checks its own API calls to catch that.

Opt-in (needs network and a browser):

    uv run --group live playwright install chromium
    GFWLINKS_LIVE=1 uv run --group live pytest tests/test_live.py

Asserted: every vessel id in the URL gets an identity, track, and event API
call naming the datasets the URL specified; no 4xx/5xx; no uncaught page error.

Not asserted: start/end dates (the app buckets them into whole years and
filters client-side, so they never echo our input) or pixels (live data and
streaming tiles make a golden screenshot a re-baselining chore -- screenshots
are saved for a human to eyeball instead).
"""

import json
import os
import pathlib
import re
import time
import urllib.parse

import pytest

import gfwlinks

SPEC = json.loads((pathlib.Path(__file__).parents[2] / "specs"
                    / "url_test_cases.json").read_text())
LIVE_CASES = [case for case in SPEC["cases"] if case.get("live")]

API_HOST = "gateway.api.globalfishingwatch.org"
# The app never requests gaps events for a vessel, even when asked (verified
# 2026-08-04, both link types). Excluded so a correct URL doesn't fail this check.
UNREQUESTED_DATASETS = {"public-global-gaps-events:v4.0"}
LOAD_TIMEOUT_S = 60
SETTLE_MS = 4000
SCREENSHOT_DIR = pathlib.Path("live-screenshots")

pytestmark = pytest.mark.skipif(
    not os.environ.get("GFWLINKS_LIVE"),
    reason="live app check; set GFWLINKS_LIVE=1 (needs network + chromium)")


def _expected(case):
    """Return (vessel_ids, datasets) that must appear in the app's own API
    calls for this case."""
    args = case["args"]
    if "vessel_ids" in args:                                      # vessel_map_url
        return args["vessel_ids"], [gfwlinks.IDENTITY_DATASET, gfwlinks.TRACKS_DATASET,
                                     *gfwlinks.EVENT_DATASETS]
    # vessel_profile_url only requests events for whichever visible_events was
    # passed, under different names (encounter -> encounters, etc.), so only the
    # two datasets that fire regardless of visible_events are checked here.
    return [args["vessel_id"]], [gfwlinks.IDENTITY_DATASET, gfwlinks.TRACKS_DATASET]


def _clear_overlays(page):
    """Dismiss the welcome modal and cookie banner so the screenshot shows the
    map, not an overlay. Best-effort: only the screenshot depends on this, so a
    failure here must never fail the test."""
    try:
        # both are ARIA dialogs (div role="dialog"), not native <dialog>, so
        # there's no close() to call -- click their own close button instead
        page.evaluate("""
            document.querySelectorAll('[role="dialog"]').forEach((modal) => {
              const button = [...modal.querySelectorAll('button')].find((b) =>
                /close|dismiss/i.test(b.getAttribute('aria-label') || b.textContent));
              if (button) button.click();
            })
        """)
        page.add_style_tag(content='[role="dialog"] { display: none !important }')
        page.wait_for_timeout(500)
    except Exception:                                      # noqa: BLE001 -- see above
        pass


@pytest.fixture(scope="session")
def browser():
    playwright = pytest.importorskip("playwright.sync_api",
                                     reason="pip install playwright")
    with playwright.sync_playwright() as driver:
        instance = driver.chromium.launch()
        yield instance
        instance.close()


def _assert_app_understands(url, vessel_ids, datasets, browser, screenshot_name):
    """Load `url` and assert the app's own API calls confirm it understood
    every vessel id and dataset. Raises AssertionError otherwise."""
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()
    api_calls, page_errors = [], []

    def record(response):
        if API_HOST in response.url:
            # unquoted so the patterns below read as the app's own param names
            api_calls.append((urllib.parse.unquote(response.url), response.status))

    page.on("response", record)
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    def seen(pattern):
        return [call for call in api_calls if re.search(pattern, call[0])]

    # maps a description of what's missing to the regex that must match
    required = {}
    for vessel_id in vessel_ids:
        quoted = re.escape(vessel_id)
        required["identity request for %s (vessel id / identity dataset)" % vessel_id] = \
            r"/v3/vessels/%s\?" % quoted
        required["track request for %s (track dataview)" % vessel_id] = \
            r"/v3/vessels/%s/tracks\?" % quoted
        required["event request for %s (event datasets)" % vessel_id] = \
            r"/v3/events\?vessels\[0\]=%s" % quoted
    for dataset in sorted(set(datasets) - UNREQUESTED_DATASETS):
        required["a request naming %s" % dataset] = re.escape(dataset)

    try:
        page.goto(url, wait_until="load")
        # events land after tracks, well after `load` -- poll the whole set so a
        # healthy run exits early and a slow one still gets its full timeout
        deadline = time.time() + LOAD_TIMEOUT_S
        while time.time() < deadline and not all(map(seen, required.values())):
            page.wait_for_timeout(500)
        _clear_overlays(page)
        # basemap tiles stream in after the track paints; let them settle
        # before the screenshot, or it shows a track over blank ocean
        page.wait_for_timeout(SETTLE_MS)
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SCREENSHOT_DIR / ("%s.png" % screenshot_name)))
        final_url = page.url
    finally:
        context.close()

    rejected = [call for call in api_calls if call[1] >= 400]
    assert not rejected, "GFW API rejected %d request(s): %s" % (
        len(rejected), rejected[:3])

    # report every missing request at once, not just the first
    missing = sorted(label for label, pattern in required.items() if not seen(pattern))
    assert not missing, ("the app never made these requests, so it no longer reads "
                         "our parameters:\n  " + "\n  ".join(missing))

    for vessel_id in vessel_ids:
        # the app rewrites the query into its own tokenized form; ids must survive that
        assert vessel_id in final_url, "%s dropped from the URL on load" % vessel_id

    assert not page_errors, "uncaught page error(s): %s" % page_errors[:3]


@pytest.mark.parametrize("case", LIVE_CASES, ids=lambda case: case["name"])
def test_app_still_understands_our_url(case, browser):
    url = getattr(gfwlinks, case["function"])(**case["args"])
    assert url == case["url"], "spec is stale -- run test_spec.py first"
    vessel_ids, datasets = _expected(case)
    _assert_app_understands(url, vessel_ids, datasets, browser, case["name"])


def test_canary_catches_a_broken_url(browser):
    """This check is only useful if it can fail. Break a real URL's dataset
    version and confirm the assertion above actually fires."""
    case = next(c for c in LIVE_CASES if c["name"] == "single_vessel_minimal")
    broken_url = case["url"].replace("v4.0", "v9.0")
    vessel_ids, datasets = _expected(case)
    with pytest.raises(AssertionError):
        _assert_app_understands(broken_url, vessel_ids, datasets, browser, "canary")
