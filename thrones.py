"""
A GAME OF THRONES — text prototype
A first playable skeleton: pick a house, and try to claim the Iron Throne
by growing your armies, waging war, and forging alliances while the other
houses scheme against you (and each other).

HOW THE COMPUTER "THINKS":
There is no machine learning here. Each AI house looks at everything it
COULD do this turn, gives every option a score based on the situation, and
does the highest-scoring thing. That is called "utility AI". Read the
choose_ai_action() function to see the enemy brain — that's the heart of it.

Run it with:  python throne.py
"""

import random
import math

# ---------------------------------------------------------------------------
# 1. THE WORLD  — every house starts alive, just like episode 1
# ---------------------------------------------------------------------------

class House:
    def __init__(self, name, seat, army, gold, regions):
        self.name = name
        self.seat = seat        # home castle (flavor)
        self.army = army        # military strength
        self.gold = gold        # pays to raise armies
        self.regions = regions  # territories held; lose them all and you're out
        self.alive = True

def make_world():
    return {
        "Stark":     House("Stark",     "Winterfell",     90, 40, 3),
        "Lannister": House("Lannister", "Casterly Rock",  75, 90, 3),
        "Baratheon": House("Baratheon", "King's Landing", 80, 50, 3),
        "Targaryen": House("Targaryen", "Dragonstone",    70, 45, 2),
        "Tyrell":    House("Tyrell",    "Highgarden",     65, 80, 2),
    }

# opinion[a][b] = how much house a likes house b, from -100 (hatred) to +100
def make_opinions(houses):
    op = {a: {b: 0 for b in houses if b != a} for a in houses}
    # a few starting rivalries and ties for flavor
    op["Stark"]["Lannister"] = -40
    op["Lannister"]["Stark"] = -40
    op["Targaryen"]["Baratheon"] = -50   # the old grudge
    op["Baratheon"]["Targaryen"] = -30
    return op

alliances = set()  # a set of frozenset({"Stark","Tyrell"}) pairs

def are_allied(a, b):
    return frozenset({a, b}) in alliances

# ---------------------------------------------------------------------------
# 2. CORE RULES  — combat, alliances, resources
# ---------------------------------------------------------------------------

def total_regions(houses):
    return sum(h.regions for h in houses.values() if h.alive)

def throne_threshold(houses):
    # hold this many regions and the realm bends the knee to you
    return math.ceil(0.6 * total_regions(houses))

def living(houses):
    return [h for h in houses.values() if h.alive]

def battle(houses, opinions, att_name, def_name):
    att, dfn = houses[att_name], houses[def_name]
    # defender gets a home-ground bonus; luck swings each side a bit
    att_power = att.army * random.uniform(0.8, 1.2)
    def_power = dfn.army * random.uniform(0.8, 1.2) * 1.15

    print(f"\n  ⚔  {att_name} marches on {def_name}!")
    # war sours relations no matter who wins
    opinions[def_name][att_name] = max(-100, opinions[def_name][att_name] - 30)
    opinions[att_name][def_name] = max(-100, opinions[att_name][def_name] - 10)

    if att_power > def_power:
        att.regions += 1
        dfn.regions -= 1
        att.army = int(att.army * 0.85)
        dfn.army = int(dfn.army * 0.65)
        print(f"     {att_name} wins the field and takes a region from {def_name}.")
        if dfn.regions <= 0:
            dfn.alive = False
            print(f"     💀 House {def_name} has been wiped from the map!")
    else:
        att.army = int(att.army * 0.7)
        dfn.army = int(dfn.army * 0.9)
        print(f"     {def_name} holds! {att_name}'s host is bloodied and thrown back.")

def try_alliance(houses, opinions, a, b):
    if are_allied(a, b):
        print(f"  {a} and {b} are already allied.")
        return
    # b accepts if it likes a enough, OR if there is a shared, stronger threat
    strongest = max(living(houses), key=lambda h: h.army)
    common_threat = strongest.name not in (a, b) and strongest.army > houses[b].army
    if opinions[b][a] >= -20 or common_threat:
        alliances.add(frozenset({a, b}))
        opinions[a][b] = min(100, opinions[a][b] + 25)
        opinions[b][a] = min(100, opinions[b][a] + 25)
        print(f"  🤝 {b} accepts an alliance with {a}.")
    else:
        print(f"  {b} spurns {a}'s offer.")

# ---------------------------------------------------------------------------
# 3. THE ENEMY BRAIN  — utility AI (no machine learning needed!)
# ---------------------------------------------------------------------------

def choose_ai_action(houses, opinions, me_name):
    """Look at every option, score it, return the best (action, target)."""
    me = houses[me_name]
    others = [h for h in living(houses) if h.name != me_name]
    avg_army = sum(h.army for h in living(houses)) / len(living(houses))

    options = []  # list of (score, action, target)

    # Option A: raise more troops — attractive when we're weak and have gold
    grow_score = 0
    if me.army < avg_army:
        grow_score = (avg_army - me.army) * 0.5
    if me.gold < 20:
        grow_score -= 20  # can't really afford it
    options.append((grow_score, "grow", None))

    # Option B: attack someone — attractive when we're stronger and dislike them
    for target in others:
        if are_allied(me_name, target.name):
            continue  # don't stab an ally in the back (yet!)
        strength_edge = me.army - target.army
        dislike = -opinions[me_name][target.name]        # more dislike = more score
        weakness = (10 - target.regions) * 3             # prey on the small
        score = strength_edge + dislike * 0.5 + weakness
        if me.army <= target.army * 0.9:
            score -= 60  # too risky, we'd probably lose
        options.append((score, "attack", target.name))

    # Option C: seek an alliance — attractive when someone dominant scares us
    strongest = max(living(houses), key=lambda h: h.army)
    if strongest.name != me_name and strongest.army > me.army * 1.2:
        for target in others:
            if target.name == strongest.name or are_allied(me_name, target.name):
                continue
            score = 40 + opinions[me_name][target.name] * 0.3
            options.append((score, "ally", target.name))

    options.sort(reverse=True, key=lambda x: x[0])
    best_score, action, target = options[0]
    if best_score <= 0:      # nothing worthwhile — bide time and tax the smallfolk
        return "tax", None
    return action, target

def run_ai_turn(houses, opinions, me_name):
    action, target = choose_ai_action(houses, opinions, me_name)
    me = houses[me_name]
    if action == "grow":
        spend = min(me.gold, 30)
        me.gold -= spend
        me.army += spend
        print(f"  {me_name} raises {spend} troops at {me.seat}.")
    elif action == "attack":
        battle(houses, opinions, me_name, target)
    elif action == "ally":
        try_alliance(houses, opinions, me_name, target)
    elif action == "tax":
        income = me.regions * 10
        me.gold += income
        print(f"  {me_name} fills its coffers (+{income} gold).")

# ---------------------------------------------------------------------------
# 4. THE PLAYER'S TURN
# ---------------------------------------------------------------------------

def show_status(houses, opinions, player):
    print("\n" + "=" * 60)
    for h in houses.values():
        if not h.alive:
            continue
        tag = " (YOU)" if h.name == player else ""
        allies = [n for n in houses if n != h.name and are_allied(h.name, n)]
        ally_str = f"  allies: {', '.join(allies)}" if allies else ""
        print(f" {h.name:<10}{tag:<6} army {h.army:<4} gold {h.gold:<4} "
              f"regions {h.regions}{ally_str}")
    print(f" Throne needs {throne_threshold(houses)} regions "
          f"(of {total_regions(houses)} in play).")
    print("=" * 60)

def player_turn(houses, opinions, player):
    me = houses[player]
    while True:
        print("\nYour move, my lord:")
        print("  1) Raise army (costs gold)")
        print("  2) Attack a house")
        print("  3) Propose an alliance")
        print("  4) Collect taxes")
        print("  5) View the realm")
        choice = input("> ").strip()

        if choice == "1":
            spend = min(me.gold, 30)
            if spend <= 0:
                print("  Your treasury is empty!")
                continue
            me.gold -= spend
            me.army += spend
            print(f"  You raise {spend} troops.")
            return
        elif choice == "2":
            targets = [h.name for h in living(houses)
                       if h.name != player and not are_allied(player, h.name)]
            if not targets:
                print("  No one left to attack!")
                continue
            for i, t in enumerate(targets, 1):
                print(f"    {i}) {t} (army {houses[t].army}, regions {houses[t].regions})")
            pick = input("  Attack which? > ").strip()
            if pick.isdigit() and 1 <= int(pick) <= len(targets):
                battle(houses, opinions, player, targets[int(pick) - 1])
                return
        elif choice == "3":
            targets = [h.name for h in living(houses)
                       if h.name != player and not are_allied(player, h.name)]
            for i, t in enumerate(targets, 1):
                print(f"    {i}) {t}")
            pick = input("  Ally with whom? > ").strip()
            if pick.isdigit() and 1 <= int(pick) <= len(targets):
                try_alliance(houses, opinions, player, targets[int(pick) - 1])
                return
        elif choice == "4":
            income = me.regions * 10
            me.gold += income
            print(f"  Your coffers swell (+{income} gold).")
            return
        elif choice == "5":
            show_status(houses, opinions, player)
        else:
            print("  The maester does not understand.")

# ---------------------------------------------------------------------------
# 5. WIN / LOSE CHECK  AND  MAIN LOOP
# ---------------------------------------------------------------------------

def check_winner(houses):
    alive = living(houses)
    if len(alive) == 1:
        return alive[0].name
    for h in alive:
        if h.regions >= throne_threshold(houses):
            return h.name
    return None

def main():
    print("""
     A GAME OF THRONES
     -----------------
     You win when you hold enough of the realm to claim the Iron Throne,
     or when every rival house is destroyed.
    """)
    houses = make_world()
    opinions = make_opinions(houses)

    print("Choose your house:")
    names = list(houses.keys())
    for i, n in enumerate(names, 1):
        h = houses[n]
        print(f"  {i}) {n:<10} (seat: {h.seat}, army {h.army}, gold {h.gold})")
    pick = input("> ").strip()
    player = names[int(pick) - 1] if pick.isdigit() and 1 <= int(pick) <= len(names) else names[0]
    print(f"\nYou rule House {player} of {houses[player].seat}. The game of thrones begins.\n")

    turn = 1
    while True:
        print(f"\n########## TURN {turn} ##########")
        show_status(houses, opinions, player)

        if houses[player].alive:
            player_turn(houses, opinions, player)
        winner = check_winner(houses)
        if winner:
            break

        # every other living house takes ONE action, using the enemy brain
        print("\n--- The other houses make their moves ---")
        for name in list(houses.keys()):
            if name != player and houses[name].alive:
                run_ai_turn(houses, opinions, name)

        winner = check_winner(houses)
        if winner:
            break
        turn += 1

    print("\n" + "#" * 40)
    if winner == player:
        print(f"  👑 House {player} sits the Iron Throne. You have won!")
    elif not houses[player].alive:
        print(f"  💀 House {player} is destroyed. Your watch has ended.")
    else:
        print(f"  👑 House {winner} claimed the throne before you could. You have lost.")
    print("#" * 40)

if __name__ == "__main__":
    main()