"""Smoke tests for the House roster — plain asserts, no pytest required.

Run:  python tests/test_house.py      (from the repo root)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from got.core import new_regions, owner_house, link_houses, resolve_battle
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


def test_link_houses_points_regions_at_their_house():
    houses = make_houses()
    regions = link_houses(new_regions(), houses)
    assert regions["The North"].house is houses["Stark"]
    assert regions["Westerlands"].house is houses["Lannister"]
    assert regions["The Vale"].house is None          # unclaimed land


def test_conquest_moves_the_house_reference_too():
    houses = make_houses()
    regions = link_houses(new_regions(), houses)
    north, vale = regions["The North"], regions["The Vale"]
    north.army, vale.army = 50, 1                      # a rout
    resolve_battle(regions, north, vale)
    assert vale.owner == "Stark"
    assert vale.house is houses["Stark"]


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
