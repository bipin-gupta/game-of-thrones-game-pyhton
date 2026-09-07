"""The House domain object.

A ``House`` is one of the great families contesting the Iron Throne. For now
it holds only identity (name, banner colour) and three raw resource counters.
Nothing here spends or earns them yet — economy and diplomacy come later.
Territories record their owner by *name* (see ``got.world.region.Region``) and
also keep a direct ``region.house`` reference to this object, wired up by
``got.core.link_houses()``.
"""

from dataclasses import dataclass


@dataclass
class House:
    name: str
    banner_color: tuple[int, int, int]
    gold: int = 0
    food: int = 0
    influence: int = 0
