import pytest

import gfwlinks


def test_visible_events_rejects_bare_string():
    with pytest.raises(TypeError, match="single string"):
        gfwlinks.vessel_profile_url("abc", visible_events="fishing")


def test_vessel_ids_rejects_bare_string():
    with pytest.raises(TypeError, match="single string"):
        gfwlinks.vessel_map_url("abc")
