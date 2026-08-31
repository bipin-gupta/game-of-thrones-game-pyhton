"""Smoke tests for the House roster — plain asserts, no pytest required.

Run:  python tests/test_house.py      (from the repo root)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from got.core import new_regions, owner_house
from got.houses import House, make_houses, NEUTRAL_COLOR


def test_make_houses_has_the_five_great_houses():
    houses = make_houses()
    assert set(houses) == {"Stark", "Lannister", "Baratheon", "Targaryen", "Tyrell"}
    for name, h in houses.items():
        assert isinstance(h, House)
        assert h.name == name
        assert len(h.banner_color) == 3
        assert h.gold == 0 and h.food == 0 and h.influence == 0


def test_make_houses_returns_a_fresh_roster_each_call():
    a, b = make_houses(), make_houses()
    assert a is not b
    a["Stark"].gold = 99
    assert b["Stark"].gold == 0


def test_owner_house_resolves_owner_name_to_house():
    houses = make_houses()
    regions = new_regions()
    assert owner_house(regions["The North"], houses) is houses["Stark"]
    assert owner_house(regions["Westerlands"], houses) is houses["Lannister"]
    # unclaimed land has no House
    assert owner_house(regions["The Vale"], houses) is None


def test_neutral_color_is_a_plain_rgb_triple():
    assert len(NEUTRAL_COLOR) == 3


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
