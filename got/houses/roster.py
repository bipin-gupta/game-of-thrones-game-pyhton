"""The starting roster of houses for a new game.

The banner colours were previously the ``HOUSE_COLORS`` dict inside
throne2d.py; they live here now so a House owns its own colour.
"""

from got.houses.house import House

# unclaimed land is not a House — it just needs a colour to draw
NEUTRAL_COLOR = (95, 100, 120)

_HOUSE_DATA = [
    # name         banner colour
    ("Stark",     (170, 175, 185)),
    ("Lannister", (200, 40, 45)),
    ("Baratheon", (235, 200, 55)),
    ("Targaryen", (35, 35, 40)),
    ("Tyrell",    (55, 160, 70)),
]


def make_houses():
    """Return the five great houses, freshly created, keyed by name."""
    return {name: House(name=name, banner_color=color)
            for name, color in _HOUSE_DATA}
