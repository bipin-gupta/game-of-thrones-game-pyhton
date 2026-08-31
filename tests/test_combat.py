"""Smoke tests for got.core — plain asserts, no pytest required.

Run:  python tests/test_combat.py      (from the repo root)
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from got.core import (
    new_regions, houses_alive, regions_of, is_border,
    resolve_battle, ai_house_turn, throne_target, check_end,
)
from got.world.region import Region


def _two_regions(src_owner, src_army, tgt_owner, tgt_army):
    return {
        "A": Region(name="A", pos=(0, 0), owner=src_owner,
                    army=src_army, neighbours=["B"]),
        "B": Region(name="B", pos=(1, 0), owner=tgt_owner,
                    army=tgt_army, neighbours=["A"]),
    }


def test_new_regions_shape():
    regions = new_regions()
    assert len(regions) == 10
    assert all(isinstance(r, Region) for r in regions.values())
    assert regions["The North"].owner == "Stark"
    assert houses_alive(regions) == {"Stark", "Lannister", "Baratheon", "Targaryen", "Tyrell"}
    assert len(regions_of(regions, "Baratheon")) == 2
    # every neighbour reference resolves to a real region
    for r in regions.values():
        for n in r.neighbours:
            assert n in regions


def test_is_border():
    regions = new_regions()
    assert is_border(regions, regions["The North"]) is True      # borders neutral land
    # a region fully surrounded by its own owner is not a border
    regions["Dragonstone"].owner = "Baratheon"                   # Dragonstone's only nbr
    assert is_border(regions, regions["Dragonstone"]) is False


def test_attacker_overwhelms_defender():
    # 20 vs 1: attack in [14, 26], defend in [0.7, 1.3] -> attacker always wins
    regions = _two_regions("Stark", 20, "Lannister", 1)
    msg = resolve_battle(regions, regions["A"], regions["B"])
    assert regions["B"].owner == "Stark"
    assert regions["B"].army == 10            # max(1, 20 // 2)
    assert regions["A"].army == 10            # 20 - 10
    assert "takes" in msg


def test_defender_holds_against_hopeless_attack():
    # 1 vs 100: attacker always loses
    regions = _two_regions("Stark", 1, "Lannister", 100)
    msg = resolve_battle(regions, regions["A"], regions["B"])
    assert regions["B"].owner == "Lannister"
    assert regions["A"].army == 1             # max(1, 1 - 2)
    assert regions["B"].army == 99            # 100 - 1
    assert "holds" in msg


def test_resolve_battle_is_deterministic_under_seed():
    random.seed(1234)
    r1 = _two_regions("Stark", 6, "Lannister", 6)
    out1 = resolve_battle(r1, r1["A"], r1["B"])
    random.seed(1234)
    r2 = _two_regions("Stark", 6, "Lannister", 6)
    out2 = resolve_battle(r2, r2["A"], r2["B"])
    assert out1 == out2
    assert r1 == r2


def test_ai_turn_reinforces_when_it_cannot_attack():
    # one weak region (army < 4 => no attack), neighbour owned by self
    regions = {
        "Home": Region(name="Home", pos=(0, 0), owner="Stark",
                       army=3, neighbours=["Keep"]),
        "Keep": Region(name="Keep", pos=(1, 0), owner="Stark",
                       army=3, neighbours=["Home"]),
    }
    log = []
    ai_house_turn(regions, "Stark", log)
    # reinforcements = max(2, len(mine)) = 2, poured into the strongpoint
    assert regions["Home"].army + regions["Keep"].army == 8
    assert log == []                             # no enemy to hit


def test_ai_turn_attacks_a_beatable_neighbour():
    regions = {
        "Home": Region(name="Home", pos=(0, 0), owner="Stark",
                       army=20, neighbours=["Foe"]),
        "Foe": Region(name="Foe", pos=(1, 0), owner="Lannister",
                      army=1, neighbours=["Home"]),
    }
    log = []
    ai_house_turn(regions, "Stark", log)
    assert regions["Foe"].owner == "Stark"       # overwhelming odds -> taken
    assert len(log) == 1


def test_ai_turn_is_noop_for_landless_house():
    regions = new_regions()
    log = []
    ai_house_turn(regions, "Nobody", log)
    assert log == []


def test_throne_target():
    assert throne_target(new_regions()) == 6     # ceil(0.6 * 10)


def test_check_end_win_lose_ongoing():
    regions = new_regions()
    assert check_end(regions, "Stark") == (None, None)

    # wipe Stark off the map -> player "Stark" loses
    for r in regions.values():
        if r.owner == "Stark":
            r.owner = "Lannister"
    assert check_end(regions, "Stark") == ("lose", None)

    # give Lannister the throne threshold -> "win" for a Lannister player
    lannister_target = throne_target(regions)
    owned = 0
    for r in regions.values():
        if owned < lannister_target:
            r.owner = "Lannister"
            owned += 1
    assert check_end(regions, "Lannister") == ("win", "Lannister")
    assert check_end(regions, "Tyrell") == ("lose", "Lannister")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
