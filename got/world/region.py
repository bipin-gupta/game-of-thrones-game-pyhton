"""The Region domain object.

A ``Region`` is one node of the map graph: a claimable territory with a
garrison and a list of the regions it borders. Regions are kept in a dict
keyed by name (see :func:`got.core.new_regions`), so a region records its
neighbours as *names* and callers resolve them through that dict.

``owner`` stays the canonical identity of who holds the territory (a house
name, or ``None``). ``house`` is an optional direct reference to the owning
``House`` object, filled in by :func:`got.core.link_houses`; combat keeps it
in step. Front-ends should prefer ``region.house`` (banner colour, resources)
over matching on the owner string.

This is a plain mutable data container — combat and the AI write ``owner``,
``house`` and ``army`` in place. It deliberately holds no game rules yet;
those still live in ``got.core``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from got.houses.house import House


@dataclass
class Region:
    name: str
    pos: tuple[int, int]                 # (x, y) on the map, in pixels for now
    owner: Optional[str]                 # house name, or None for unclaimed land
    army: int                            # garrison strength
    neighbours: list[str] = field(default_factory=list)
    house: Optional["House"] = None      # owning House object, once linked
