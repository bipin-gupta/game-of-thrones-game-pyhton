"""
A GAME OF THRONES — 2D map prototype (Pygame)
----------------------------------------------
The next step up from the text version: a clickable map of Westeros.
Regions are circles connected by roads. You own the coloured ones; conquer
your way to the throne by reinforcing your borders and attacking neighbours.
The other houses take their turns with the same "utility AI" idea as before.

Everything is drawn with simple shapes and text, so it runs with NO art files
needed. When you want real art, you swap the circles for image sprites (see the
note near draw_region).

SETUP:  pip install pygame
RUN:    python throne2d.py
"""

import sys
import random
import pygame

# ---------------------------------------------------------------------------
# 1. LOOK & FEEL
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 1000, 720
MAP_W = 640                      # the map fills the left side; panel on the right
FPS = 30

# each house has a banner colour
HOUSE_COLORS = {
    "Stark":     (170, 175, 185),
    "Lannister": (200, 40, 45),
    "Baratheon": (235, 200, 55),
    "Targaryen": (35, 35, 40),
    "Tyrell":    (55, 160, 70),
    None:        (95, 100, 120),   # neutral, unclaimed land
}
BG        = (26, 30, 42)
PANEL_BG  = (18, 21, 30)
ROAD      = (70, 78, 96)
WHITE     = (235, 238, 245)
DIM       = (150, 156, 168)
HILITE    = (255, 240, 150)

# ---------------------------------------------------------------------------
# 2. THE MAP  — regions roughly placed like Westeros, north at the top
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
        regions[name] = {"name": name, "pos": (x, y), "owner": owner,
                         "army": army, "neighbours": nbrs}
    return regions

def houses_alive(regions):
    return {r["owner"] for r in regions.values() if r["owner"] is not None}

def regions_of(regions, house):
    return [r for r in regions.values() if r["owner"] == house]

def is_border(regions, region):
    """A region is a border if any neighbour is owned by someone else."""
    return any(regions[n]["owner"] != region["owner"] for n in region["neighbours"])

# ---------------------------------------------------------------------------
# 3. COMBAT  — the same idea as the text version: strength + a little luck
# ---------------------------------------------------------------------------

def resolve_battle(regions, src, tgt):
    attack  = src["army"] * random.uniform(0.7, 1.3)
    defend  = tgt["army"] * random.uniform(0.7, 1.3)
    if attack > defend:
        moved = max(1, src["army"] // 2)   # half the host marches into the new land
        tgt["owner"] = src["owner"]
        tgt["army"]  = moved
        src["army"] -= moved
        return f"{src['owner']} takes {tgt['name']}!"
    else:
        src["army"] = max(1, src["army"] - 2)
        tgt["army"] = max(1, tgt["army"] - 1)
        return f"{tgt['name']} holds against {src['owner']}."

# ---------------------------------------------------------------------------
# 4. THE ENEMY BRAIN  — one turn for one AI house (utility AI, no ML)
# ---------------------------------------------------------------------------

def ai_house_turn(regions, house, log):
    mine = regions_of(regions, house)
    if not mine:
        return
    # Reinforce: pour new troops into the strongest border region.
    reinforcements = max(2, len(mine))
    borders = [r for r in mine if is_border(regions, r)] or mine
    strongpoint = max(borders, key=lambda r: r["army"])
    strongpoint["army"] += reinforcements

    # Attack: from each region, hit the weakest neighbour we can likely beat.
    for r in sorted(mine, key=lambda r: r["army"], reverse=True):
        if r["army"] < 4:
            continue
        enemies = [regions[n] for n in r["neighbours"]
                   if regions[n]["owner"] != house]
        if not enemies:
            continue
        target = min(enemies, key=lambda e: e["army"])
        if r["army"] > target["army"] * 1.15:      # only if confident
            log.append(ai_prefix(resolve_battle(regions, r, target)))

def ai_prefix(msg):
    return "  " + msg

# ---------------------------------------------------------------------------
# 5. DRAWING
# ---------------------------------------------------------------------------

def draw_region(screen, font, region, selected, reachable):
    x, y = region["pos"]
    color = HOUSE_COLORS[region["owner"]]
    radius = 34
    # ---- To use REAL ART later: instead of this circle, blit a sprite here,
    # ---- e.g.  screen.blit(house_banner_image[region["owner"]], (x-32, y-32))
    pygame.draw.circle(screen, color, (x, y), radius)
    ring = HILITE if selected else (WHITE if reachable else (0, 0, 0))
    pygame.draw.circle(screen, ring, (x, y), radius, 3 if (selected or reachable) else 2)

    # region name above, army count in the middle
    label = font.render(region["name"], True, WHITE)
    screen.blit(label, (x - label.get_width() // 2, y - radius - 18))
    # dark text on the pale yellow Baratheon banner so it stays readable
    num_color = (20, 20, 20) if region["owner"] in ("Baratheon", "Stark") else WHITE
    num = font.render(str(region["army"]), True, num_color)
    screen.blit(num, (x - num.get_width() // 2, y - num.get_height() // 2))

def draw_map(screen, font, regions, selected, reachable_names):
    drawn = set()
    for r in regions.values():                       # roads first, under the circles
        for n in r["neighbours"]:
            edge = frozenset({r["name"], n})
            if edge not in drawn:
                pygame.draw.line(screen, ROAD, r["pos"], regions[n]["pos"], 3)
                drawn.add(edge)
    for r in regions.values():
        draw_region(screen, font, r,
                    selected == r["name"],
                    r["name"] in reachable_names)

def draw_panel(screen, big, font, small, regions, player, phase, pool, log):
    px = MAP_W
    pygame.draw.rect(screen, PANEL_BG, (px, 0, WIDTH - px, HEIGHT))
    y = 24
    title = big.render(f"House {player}", True, HOUSE_COLORS[player])
    screen.blit(title, (px + 24, y)); y += 46

    owned = len(regions_of(regions, player))
    total = len(regions)
    screen.blit(font.render(f"Regions: {owned} / {total}", True, WHITE), (px + 24, y)); y += 26
    screen.blit(font.render(f"Throne needs: {throne_target(regions)}", True, DIM), (px + 24, y)); y += 34

    # whose turn / what to do
    if phase == "reinforce":
        screen.blit(font.render(f"REINFORCE  ({pool} left)", True, HILITE), (px + 24, y)); y += 24
        screen.blit(small.render("Click your regions to add troops.", True, DIM), (px + 24, y)); y += 20
    else:
        screen.blit(font.render("ATTACK", True, HILITE), (px + 24, y)); y += 24
        screen.blit(small.render("Click a region, then a neighbour to attack.", True, DIM), (px + 24, y)); y += 20
    y += 12

    # the action button
    btn = pygame.Rect(px + 24, y, WIDTH - px - 48, 40)
    pygame.draw.rect(screen, (60, 68, 92), btn, border_radius=6)
    txt = "Skip to Attack" if phase == "reinforce" else "End Turn"
    t = font.render(txt, True, WHITE)
    screen.blit(t, (btn.centerx - t.get_width() // 2, btn.centery - t.get_height() // 2))
    y += 58

    # message log
    screen.blit(font.render("Chronicle:", True, WHITE), (px + 24, y)); y += 24
    for line in log[-11:]:
        screen.blit(small.render(line[:42], True, DIM), (px + 24, y)); y += 18
    return btn

# ---------------------------------------------------------------------------
# 6. WIN / LOSE
# ---------------------------------------------------------------------------

def throne_target(regions):
    import math
    return math.ceil(0.6 * len(regions))

def check_end(regions, player):
    alive = houses_alive(regions)
    if player not in alive:
        return ("lose", None)
    for h in alive:
        if len(regions_of(regions, h)) >= throne_target(regions):
            return ("win" if h == player else "lose", h)
    return (None, None)

# ---------------------------------------------------------------------------
# 7. SCREENS
# ---------------------------------------------------------------------------

def region_at(regions, pos):
    for r in regions.values():
        dx, dy = pos[0] - r["pos"][0], pos[1] - r["pos"][1]
        if dx * dx + dy * dy <= 34 * 34:
            return r
    return None

def choose_house_screen(screen, big, font):
    houses = [h for h in HOUSE_COLORS if h is not None]
    buttons = []
    while True:
        screen.fill(BG)
        title = big.render("Choose your house", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
        buttons = []
        for i, h in enumerate(houses):
            rect = pygame.Rect(WIDTH // 2 - 150, 200 + i * 70, 300, 54)
            pygame.draw.rect(screen, HOUSE_COLORS[h], rect, border_radius=8)
            label = big.render(h, True, (15, 15, 15) if h in ("Baratheon", "Stark") else WHITE)
            screen.blit(label, (rect.centerx - label.get_width() // 2,
                                rect.centery - label.get_height() // 2))
            buttons.append((rect, h))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                for rect, h in buttons:
                    if rect.collidepoint(e.pos):
                        return h

def end_screen(screen, big, result, who):
    while True:
        screen.fill(BG)
        if result == "win":
            msg, col = "You have won the Iron Throne!", HILITE
        else:
            msg, col = f"House {who} took the throne. You have lost.", (200, 80, 80)
        t = big.render(msg, True, col)
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 20))
        hint = big.render("Close the window to exit.", True, DIM)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 30))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

# ---------------------------------------------------------------------------
# 8. MAIN GAME LOOP
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("A Game of Thrones — 2D prototype")
    big   = pygame.font.SysFont("georgia", 26, bold=True)
    font  = pygame.font.SysFont("georgia", 18)
    small = pygame.font.SysFont("consolas", 14)
    clock = pygame.time.Clock()

    player = choose_house_screen(screen, big, font)
    regions = new_regions()
    log = [f"House {player} rises. The game begins."]

    phase = "reinforce"
    pool = max(2, len(regions_of(regions, player)))
    selected = None                    # region name chosen as attack source

    running = True
    while running:
        # ---- what can the player currently click as a valid target? (for glow)
        reachable = set()
        if phase == "attack" and selected:
            for n in regions[selected]["neighbours"]:
                if regions[n]["owner"] != player:
                    reachable.add(n)

        # ---- draw everything
        screen.fill(BG)
        draw_map(screen, font, regions, selected, reachable)
        button = draw_panel(screen, big, font, small, regions, player, phase, pool, log)
        pygame.display.flip()
        clock.tick(FPS)

        # ---- handle input
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if button.collidepoint(e.pos):
                    # the action button ends the current phase
                    if phase == "reinforce":
                        phase = "attack"
                    else:
                        # ---- run every other house's turn
                        log.append("— The other houses move —")
                        for h in [x for x in houses_alive(regions) if x != player]:
                            ai_house_turn(regions, h, log)
                        result, who = check_end(regions, player)
                        if result:
                            end_screen(screen, big, result, who)
                        # ---- start the player's next turn
                        phase = "reinforce"
                        pool = max(2, len(regions_of(regions, player)))
                        selected = None
                    continue

                clicked = region_at(regions, e.pos)
                if not clicked:
                    continue

                if phase == "reinforce":
                    if clicked["owner"] == player and pool > 0:
                        clicked["army"] += 1
                        pool -= 1
                        if pool == 0:
                            phase = "attack"
                elif phase == "attack":
                    if clicked["owner"] == player and clicked["army"] > 1:
                        selected = clicked["name"]          # pick the attacking region
                    elif selected and clicked["name"] in regions[selected]["neighbours"] \
                            and clicked["owner"] != player:
                        log.append(resolve_battle(regions, regions[selected], clicked))
                        result, who = check_end(regions, player)
                        if result:
                            end_screen(screen, big, result, who)
                        selected = None

    pygame.quit()

if __name__ == "__main__":
    main()