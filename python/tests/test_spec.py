import json
import pathlib

import pytest

import gfwlinks

SPEC = json.loads((pathlib.Path(__file__).parents[2] / "specs"
                    / "url_test_cases.json").read_text())


@pytest.mark.parametrize("case", SPEC["cases"], ids=lambda c: c["name"])
def test_url(case):
    assert getattr(gfwlinks, case["function"])(**case["args"]) == case["url"]
