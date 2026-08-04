import json
import pathlib

import pytest

import gfwlinks

SPEC = json.loads((pathlib.Path(__file__).parents[2] / "specs"
                    / "url_test_cases.json").read_text())


@pytest.mark.parametrize("case", SPEC["cases"], ids=lambda c: c["name"])
def test_url(case):
    fn = getattr(gfwlinks, case["function"])
    if "raises_matching" in case:
        with pytest.raises((ValueError, TypeError), match=case["raises_matching"]):
            fn(**case["args"])
    else:
        assert fn(**case["args"]) == case["url"]
