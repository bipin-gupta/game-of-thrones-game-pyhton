"""Pure game logic for the 2D prototype — no pygame, no rendering, no input.

Everything here operates on ``Region`` objects (see ``got.world.region``)
produced by ``new_regions()``. The ``regions`` argument passed around is a
dict mapping region name -> Region; a region records its owner and its
neighbours by *name*. A ``houses`` argument, where present, is the roster
dict from ``got.houses.make_houses()`` (name -> House).

These functions were extracted from ``throne2d.py`` so the pygame front-end
and any future front-end can share one rules implementation.
"""

import math
import random

from got.world.region import Region

# ---------------------------------------------------------------------------
# THE MAP  — regions roughly placed like Westeros, north at the top
# ---------------------------------------------------------------------------
# Each region: a name, screen position, who owns it, its garrison strength,
# and the names of the regions it borders (you can only attack neighbours).


def new_regions():
    data = [
        # name           x    y   owner        army  neighbours
        ("The North",    210,  80, "Stark",      6, ["The Vale", "Riverlands", "Iron Islands"]),
        ("Iron Islands", 100, 210, None,         3, ["The North", "Riverlands", "Westerlands"]),
        ("The Vale",     360, 150, None,         3, ["The North", "Riverlands"]),
        ("Riverlands",   240, 250, None,         3, ["The North", "The Vale", "Iron Islands",
                                                     "Westerlands", "Crownlands", "The Reach"]),
        ("Westerlands",  140, 350, "Lannister",  6, ["Iron Islands", "Riverlands", "The Reach"]),
        ("Crownlands",   380, 320, "Baratheon",  6, ["Riverlands", "The Reach", "Stormlands",
                                                     "Dragonstone"]),
        ("The Reach",    210, 450, "Tyrell",     6, ["Westerlands", "Riverlands", "Crownlands",
                                                     "Stormlands", "Dorne"]),
        ("Stormlands",   400, 460, "Baratheon",  5, ["The Reach", "Crownlands", "Dorne"]),
        ("Dragonstone",  500, 300, "Targaryen",  6, ["Crownlands"]),
        ("Dorne",        300, 590, None,         3, ["The Reach", "Stormlands"]),
    ]
    regions = {}
    for name, x, y, owner, army, nbrs in data:
        regions[name] = Region(name=name, pos=(x, y), owner=owner,
                               army=army, neighbours=list(nbrs))
    return regions


def houses_alive(regions):
    return {r.owner for r in regions.values() if r.owner is not None}


def regions_of(regions, house):
    return [r for r in regions.values() if r.owner == house]


def owner_house(region, houses):
    """The House object that owns this region, or None for unclaimed land."""
    if region.owner is None:
        return None
    return houses.get(region.owner)


def is_border(regions, region):
    """A region is a border if any neighbour is owned by someone else."""
    return any(regions[n].owner != region.owner for n in region.neighbours)


# ---------------------------------------------------------------------------
# COMBAT  — strength + a little luck
# ---------------------------------------------------------------------------


def resolve_battle(regions, src, tgt):
    attack  = src.army * random.uniform(0.7, 1.3)
    defend  = tgt.army * random.uniform(0.7, 1.3)
    if attack > defend:
        moved = max(1, src.army // 2)   # half the host marches into the new land
        tgt.owner = src.owner
        tgt.army  = moved
        src.army -= moved
        return f"{src.owner} takes {tgt.name}!"
    else:
        src.army = max(1, src.army - 2)
        tgt.army = max(1, tgt.army - 1)
        return f"{tgt.name} holds against {src.owner}."


# ---------------------------------------------------------------------------
# THE ENEMY BRAIN  — one turn for one AI house (utility AI, no ML)
# ---------------------------------------------------------------------------


def ai_house_turn(regions, house, log):
    mine = regions_of(regions, house)
    if not mine:
        return
    # Reinforce: pour new troops into the strongest border region.
    reinforcements = max(2, len(mine))
    borders = [r for r in mine if is_border(regions, r)] or mine
    strongpoint = max(borders, key=lambda r: r.army)
    strongpoint.army += reinforcements

    # Attack: from each region, hit the weakest neighbour we can likely beat.
    for r in sorted(mine, key=lambda r: r.army, reverse=True):
        if r.army < 4:
            continue
        enemies = [regions[n] for n in r.neighbours
                   if regions[n].owner != house]
        if not enemies:
            continue
        target = min(enemies, key=lambda e: e.army)
        if r.army > target.army * 1.15:      # only if confident
            log.append(ai_prefix(resolve_battle(regions, r, target)))


def ai_prefix(msg):
    return "  " + msg


# ---------------------------------------------------------------------------
# WIN / LOSE
# ---------------------------------------------------------------------------


def throne_target(regions):
    return math.ceil(0.6 * len(regions))


def check_end(regions, player):
    alive = houses_alive(regions)
    if player not in alive:
        return ("lose", None)
    for h in alive:
        if len(regions_of(regions, h)) >= throne_target(regions):
            return ("win" if h == player else "lose", h)
    return (None, None)
