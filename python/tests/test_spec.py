import json
import pathlib

import pytest

import gfwlinks

SPEC = json.loads((pathlib.Path(__file__).parents[2] / "specs"
                    / "url_test_cases.json").read_text())


def test_every_case_declares_live():
    """`live` gates test_live.py's browser checks, and its absence reads as
    "off" -- so a new case silently skips them unless it opts in or out here."""
    undeclared = [case["name"] for case in SPEC["cases"] if "live" not in case]
    assert not undeclared, ("every spec case must declare \"live\" true/false; "
                            f"missing on: {undeclared}")


@pytest.mark.parametrize("case", SPEC["cases"], ids=lambda c: c["name"])
def test_url(case):
    fn = getattr(gfwlinks, case["function"])
    if "raises_matching" in case:
        with pytest.raises((ValueError, TypeError), match=case["raises_matching"]):
            fn(**case["args"])
    else:
        assert fn(**case["args"]) == case["url"]
