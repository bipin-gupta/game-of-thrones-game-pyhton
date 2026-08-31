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
import pygame

from got.core import (
    new_regions, houses_alive, regions_of, is_border, owner_house,
    resolve_battle, ai_house_turn, throne_target, check_end,
)
from got.houses import make_houses, NEUTRAL_COLOR

# ---------------------------------------------------------------------------
# 1. LOOK & FEEL
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 1000, 720
MAP_W = 640                      # the map fills the left side; panel on the right
FPS = 30

# the five great houses (name -> House); each House carries its banner colour.
# A territory names its owner; owner_house(region, HOUSES) resolves it to the House.
HOUSES = make_houses()

BG        = (26, 30, 42)
PANEL_BG  = (18, 21, 30)
ROAD      = (70, 78, 96)
WHITE     = (235, 238, 245)
DIM       = (150, 156, 168)
HILITE    = (255, 240, 150)

# ---------------------------------------------------------------------------
# 2. MAP / COMBAT / AI / WIN-LOSE  — see got/core.py
# ---------------------------------------------------------------------------
# The pure game logic (new_regions, houses_alive, regions_of, is_border,
# owner_house, resolve_battle, ai_house_turn, throne_target, check_end) lives in
# got/core.py; the House roster lives in got/houses/. This module keeps only the
# pygame front-end: drawing, input, screens, and the main loop.

# ---------------------------------------------------------------------------
# 3. DRAWING
# ---------------------------------------------------------------------------

def draw_region(screen, font, region, selected, reachable):
    x, y = region.pos
    house = owner_house(region, HOUSES)
    color = house.banner_color if house else NEUTRAL_COLOR
    radius = 34
    # ---- To use REAL ART later: instead of this circle, blit a sprite here,
    # ---- e.g.  screen.blit(house_banner_image[region.owner], (x-32, y-32))
    pygame.draw.circle(screen, color, (x, y), radius)
    ring = HILITE if selected else (WHITE if reachable else (0, 0, 0))
    pygame.draw.circle(screen, ring, (x, y), radius, 3 if (selected or reachable) else 2)

    # region name above, army count in the middle
    label = font.render(region.name, True, WHITE)
    screen.blit(label, (x - label.get_width() // 2, y - radius - 18))
    # dark text on the pale yellow Baratheon banner so it stays readable
    num_color = (20, 20, 20) if region.owner in ("Baratheon", "Stark") else WHITE
    num = font.render(str(region.army), True, num_color)
    screen.blit(num, (x - num.get_width() // 2, y - num.get_height() // 2))

def draw_map(screen, font, regions, selected, reachable_names):
    drawn = set()
    for r in regions.values():                       # roads first, under the circles
        for n in r.neighbours:
            edge = frozenset({r.name, n})
            if edge not in drawn:
                pygame.draw.line(screen, ROAD, r.pos, regions[n].pos, 3)
                drawn.add(edge)
    for r in regions.values():
        draw_region(screen, font, r,
                    selected == r.name,
                    r.name in reachable_names)

def draw_panel(screen, big, font, small, regions, player, phase, pool, log):
    px = MAP_W
    pygame.draw.rect(screen, PANEL_BG, (px, 0, WIDTH - px, HEIGHT))
    y = 24
    title = big.render(f"House {player}", True, HOUSES[player].banner_color)
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
# 4. SCREENS
# ---------------------------------------------------------------------------

def region_at(regions, pos):
    for r in regions.values():
        dx, dy = pos[0] - r.pos[0], pos[1] - r.pos[1]
        if dx * dx + dy * dy <= 34 * 34:
            return r
    return None

def choose_house_screen(screen, big, font):
    houses = list(HOUSES)
    buttons = []
    while True:
        screen.fill(BG)
        title = big.render("Choose your house", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
        buttons = []
        for i, h in enumerate(houses):
            rect = pygame.Rect(WIDTH // 2 - 150, 200 + i * 70, 300, 54)
            pygame.draw.rect(screen, HOUSES[h].banner_color, rect, border_radius=8)
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
# 5. MAIN GAME LOOP
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
            for n in regions[selected].neighbours:
                if regions[n].owner != player:
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
                    if clicked.owner == player and pool > 0:
                        clicked.army += 1
                        pool -= 1
                        if pool == 0:
                            phase = "attack"
                elif phase == "attack":
                    if clicked.owner == player and clicked.army > 1:
                        selected = clicked.name             # pick the attacking region
                    elif selected and clicked.name in regions[selected].neighbours \
                            and clicked.owner != player:
                        log.append(resolve_battle(regions, regions[selected], clicked))
                        result, who = check_end(regions, player)
                        if result:
                            end_screen(screen, big, result, who)
                        selected = None

    pygame.quit()

if __name__ == "__main__":
    main()