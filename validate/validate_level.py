#!/usr/bin/env python3
"""
validate_level.py — a health-check tool for your level design JSON files.

You do NOT need to know how to code to use this. Run it after you (or anyone
on the team) edits a level file, and it will tell you in plain language what,
if anything, is broken — before it becomes a bug someone finds by playing the
level.

NEW HERE? START WITH:
    python3 validate_level.py --guide

That prints a plain-language walkthrough of every term this tool uses and
every command it supports, with examples. This header comment is the
technical reference for anyone who wants it, but --guide is the friendlier
version.
"""

import argparse
import json
import sys
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# GLOSSARY — plain-language explanations, shown by --guide and --explain,
# and auto-attached under any check that finds a problem in a normal run.
# If you're a level designer and not a programmer, this is the part of the
# file meant for you. Everything below this is code.
# ---------------------------------------------------------------------------
GLOSSARY = {
    "A:metrics-drift": {
        "title": "Metrics Drift",
        "plain": (
            "The level file has a 'summary' section (level_balance_metrics) "
            "that's supposed to describe the level — e.g. 'there are 36 "
            "containers, 16 of them empty.' This check recounts everything "
            "by hand and compares it to what the summary claims. If someone "
            "adds or removes a container/enemy and forgets to update the "
            "summary, this is how it gets caught."
        ),
        "why_it_matters": (
            "A wrong summary doesn't break the game, but it breaks anyone's "
            "ability to trust the numbers when tuning pacing/difficulty."
        ),
    },
    "B:tier-ceiling": {
        "title": "Tier Ceiling",
        "plain": (
            "Items and weapons are ranked in 'tiers' (0 = basic trash, "
            "3 = end-game/rare). Each zone of the level (alley, school, "
            "docks) has a maximum tier it's allowed to hand out — e.g. the "
            "alley shouldn't be handing out a Magnum. This check flags any "
            "item placed above its zone's allowed tier."
        ),
        "why_it_matters": (
            "If a high-tier item leaks into an early zone, players can "
            "become overpowered too soon and the intended difficulty curve "
            "collapses."
        ),
    },
    "C:orphan-rooms": {
        "title": "Orphaned Rooms",
        "plain": (
            "The level has a 'hub' room that everything is meant to "
            "connect back to (like a home base). This check walks every "
            "door/connection in the level and makes sure every room can "
            "actually be reached from the hub, AND that every room has some "
            "way back to the hub. A room that fails this is either "
            "unreachable (players can never get to it) or a one-way trap "
            "(players get stuck once they enter)."
        ),
        "why_it_matters": (
            "This catches level-layout mistakes — a forgotten door, a "
            "connection typo — that would soft-lock or completely hide "
            "content from a player."
        ),
    },
    "D:dangling-requirement": {
        "title": "Dangling Requirement",
        "plain": (
            "Puzzles and shortcuts in the level require a specific item "
            "(e.g. a fuse, a keycard) to unlock. This check makes sure that "
            "every required item is actually placed somewhere in the level "
            "as a pickup. If a puzzle asks for an item that was never "
            "placed anywhere, that puzzle is literally impossible to solve."
        ),
        "why_it_matters": (
            "This is the most serious kind of bug this tool can catch: it "
            "means the level cannot be completed as designed."
        ),
    },
    "E:damage-potential": {
        "title": "Damage Potential / Ammo Supply Ratio",
        "plain": (
            "Adds up every weapon in the level and how much total damage "
            "it could deal using all the ammo that's placed for it, then "
            "compares that to the total health of every enemy in the "
            "level. A ratio of 1.0 means 'just enough ammo to kill "
            "everything once, with nothing to spare.' A ratio of 7.5 means "
            "'enough ammo to kill everything about 7.5 times over.'"
        ),
        "why_it_matters": (
            "This isn't a pass/fail bug check — it's a tuning signal. A "
            "very high ratio may mean the level feels too generous for a "
            "survival-horror pacing goal; a ratio under 1.0 may mean the "
            "level is unwinnable through fair play alone."
        ),
    },
}

TERMS = {
    "hub": "The central room the level is designed to loop back to — most "
           "paths branch off from and reconnect to it.",
    "zone": "A named section of the level (e.g. alley, school, docks) used "
            "to group rooms for difficulty/reward tuning.",
    "tier": "A 0-3 ranking of how powerful/rare an item is. 0 = common "
            "trash, 3 = rare/end-game.",
    "container": "Any searchable object in a room (locker, crate, drawer, "
                 "etc.) that may or may not contain an item.",
    "puzzle gate": "A locked door/obstacle that requires a specific item "
                   "to open, used to control the order players see content.",
    "backtracking loop": "A one-way shortcut that only unlocks after a "
                          "player reaches a certain point, letting them "
                          "return to an earlier area faster than they got "
                          "there the first time.",
    "strict mode": "A setting (--strict) that makes the tool return an "
                   "error/failure signal if ANY problem is found — meant "
                   "for automated systems, not for reading yourself.",
    "write-metrics": "A setting (--write-metrics) that fixes the summary "
                     "numbers automatically and saves a new corrected copy "
                     "of the file, instead of just reporting the problem.",
}


def print_guide():
    print("=" * 72)
    print("VALIDATE_LEVEL.PY — PLAIN-LANGUAGE GUIDE")
    print("=" * 72)
    print(
        "\nThis tool reads a level design JSON file and checks it for "
        "problems a designer would otherwise only discover by playtesting "
        "(or worse, a player finding them first).\n"
    )

    print("-" * 72)
    print("COMMANDS YOU CAN RUN")
    print("-" * 72)
    print(
        "\n1) Basic check — just tell me what's wrong:\n"
        "   python3 validate_level.py my_level.json\n"
        "\n"
        "2) Also check item tiers & ammo balance (recommended — needs your\n"
        "   item catalog file):\n"
        "   python3 validate_level.py my_level.json --item-tiers item_tiers.json\n"
        "\n"
        "3) Quick condensed version — one line per category, for a fast\n"
        "   glance instead of the full detailed report:\n"
        "   python3 validate_level.py my_level.json --summary\n"
        "\n"
        "4) Just show me basic stats about the level, no pass/fail judgment\n"
        "   (room count, item count, etc.) — useful as a sanity check after\n"
        "   a big edit:\n"
        "   python3 validate_level.py my_level.json --stats\n"
        "\n"
        "5) Fix the summary numbers automatically and save a corrected copy\n"
        "   (never overwrites your original file):\n"
        "   python3 validate_level.py my_level.json --write-metrics\n"
        "\n"
        "6) Explain one specific problem code you saw in a report, e.g. you\n"
        "   saw '[D:dangling-requirement]' and want to know what that means:\n"
        "   python3 validate_level.py --explain D\n"
        "\n"
        "7) This guide:\n"
        "   python3 validate_level.py --guide\n"
        "\n"
        "8) Full list of every term/code with explanations:\n"
        "   python3 validate_level.py --glossary\n"
    )

    print("-" * 72)
    print("KEY TERMS")
    print("-" * 72)
    for term, definition in TERMS.items():
        print(f"\n  {term.upper()}")
        print(f"    {definition}")

    print("\n" + "-" * 72)
    print("WHAT EACH CHECK MEANS")
    print("-" * 72)
    for code, info in GLOSSARY.items():
        print(f"\n  [{code}] {info['title']}")
        print(f"    {info['plain']}")
        print(f"    Why it matters: {info['why_it_matters']}")

    print("\n" + "=" * 72)
    print(
        "Tip: you don't need to memorize any of this. Just run the tool "
        "normally — every problem it finds already includes a plain-English "
        "explanation right under it in the report."
    )
    print("=" * 72)


def print_glossary():
    print("=" * 72)
    print("GLOSSARY — every term and check code this tool uses")
    print("=" * 72)
    for term, definition in TERMS.items():
        print(f"\n{term.upper()}")
        print(f"  {definition}")
    print()
    for code, info in GLOSSARY.items():
        print(f"\n[{code}] {info['title']}")
        print(f"  {info['plain']}")
        print(f"  Why it matters: {info['why_it_matters']}")


def print_explain(code):
    code = code.upper()
    matches = [c for c in GLOSSARY if c.upper().startswith(code)]
    if not matches:
        print(f"No check found matching '{code}'.")
        print("Valid codes: " + ", ".join(GLOSSARY.keys()))
        return
    for c in matches:
        info = GLOSSARY[c]
        print(f"[{c}] {info['title']}")
        print(f"  {info['plain']}")
        print(f"  Why it matters: {info['why_it_matters']}")
        print()


# ---------------------------------------------------------------------------
# Fallback zone map. Prefer passing --zone-map for anything beyond this one
# known level. See LIMITATIONS below.
# ---------------------------------------------------------------------------
DEFAULT_ZONE_MAP = {
    "RM_01_ALLEYWAY": "alley",
    "HW_01_BASEMENT_VENT": "alley",
    "RM_02_MAIN_VESTIBULE": "school",
    "RM_02_ADMISSIONS": "school",
    "HW_02_CENTRAL_CONCOURSE": "school",
    "RM_03_LAB_A": "school",
    "RM_03_JANITOR_NORTH": "school",
    "RM_04_PRINCIPAL": "school",
    "HW_03_LOADING_CORRIDOR": "docks",
    "RM_05_LOADING_DOCK": "docks",
}


class Report:
    """Collects findings and renders a readable, exit-code-friendly report."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, check, msg):
        self.errors.append((check, msg))

    def warn(self, check, msg):
        self.warnings.append((check, msg))

    def note(self, check, msg):
        self.info.append((check, msg))

    def has_problems(self):
        return bool(self.errors or self.warnings)

    def _categories_seen(self):
        seen = []
        for check, _ in self.errors + self.warnings:
            if check not in seen:
                seen.append(check)
        return seen

    def render(self, explain=True):
        lines = []
        lines.append("=" * 72)
        lines.append("LEVEL VALIDATION REPORT")
        lines.append("=" * 72)

        if not self.errors and not self.warnings:
            lines.append("\n✅ No errors or warnings found.\n")
        else:
            if self.errors:
                lines.append(f"\n❌ ERRORS ({len(self.errors)})")
                for check, msg in self.errors:
                    lines.append(f"   [{check}] {msg}")
            if self.warnings:
                lines.append(f"\n⚠️  WARNINGS ({len(self.warnings)})")
                for check, msg in self.warnings:
                    lines.append(f"   [{check}] {msg}")

        if self.info:
            lines.append(f"\nℹ️  INFO ({len(self.info)})")
            for check, msg in self.info:
                lines.append(f"   [{check}] {msg}")

        if explain and self._categories_seen():
            lines.append("\n" + "-" * 72)
            lines.append("WHAT THIS MEANS (plain language)")
            lines.append("-" * 72)
            for check in self._categories_seen():
                info = GLOSSARY.get(check)
                if info:
                    lines.append(f"\n[{check}] {info['title']}")
                    lines.append(f"  {info['plain']}")

        lines.append("\n" + "=" * 72)
        if self.has_problems():
            lines.append(
                "Need more detail on any of this? Run with --explain <code> "
                "(e.g. --explain D), or --guide for the full walkthrough."
            )
            lines.append("=" * 72)
        return "\n".join(lines)

    def render_summary(self):
        """Condensed one-line-per-category view for a quick glance."""
        by_check = defaultdict(lambda: {"errors": 0, "warnings": 0})
        for check, _ in self.errors:
            by_check[check]["errors"] += 1
        for check, _ in self.warnings:
            by_check[check]["warnings"] += 1

        lines = ["=" * 72, "LEVEL VALIDATION — QUICK SUMMARY", "=" * 72, ""]
        all_checks = list(GLOSSARY.keys())
        for check in all_checks:
            title = GLOSSARY[check]["title"]
            counts = by_check.get(check)
            if not counts:
                lines.append(f"  ✅ {title}: OK")
            else:
                parts = []
                if counts["errors"]:
                    parts.append(f"{counts['errors']} error(s)")
                if counts["warnings"]:
                    parts.append(f"{counts['warnings']} warning(s)")
                mark = "❌" if counts["errors"] else "⚠️"
                lines.append(f"  {mark} {title}: {', '.join(parts)}")
        lines.append("")
        lines.append(
            "Run without --summary for full details, or --explain <code> "
            "for what any of these mean."
        )
        lines.append("=" * 72)
        return "\n".join(lines)


def get_zone_map(args):
    if args.zone_map:
        with open(args.zone_map) as f:
            return json.load(f)
    return DEFAULT_ZONE_MAP


def collect_containers(level):
    """Returns list of (room_id, entity, is_empty, zone) for every container."""
    out = []
    for room in level.get("spatial_nodes", []):
        for e in room.get("functional_entities", []):
            if e.get("type") == "Container":
                out.append((room["room_id"], e, not e.get("items")))
    return out


# ---------------------------------------------------------------------------
# A. Metrics drift
# ---------------------------------------------------------------------------
def check_metrics_drift(level, report):
    containers = collect_containers(level)
    actual_total = len(containers)
    actual_empty = sum(1 for _, _, empty in containers if empty)

    actual_enemy_hp = sum(
        enemy.get("health", 0)
        for room in level.get("spatial_nodes", [])
        for enemy in room.get("enemies", [])
    )

    declared = level.get("level_balance_metrics", {})
    declared_total = declared.get("total_containers")
    declared_empty = declared.get("empty_containers")
    declared_hp = declared.get("total_enemy_hp")

    if declared_total != actual_total:
        report.error(
            "A:metrics-drift",
            f"total_containers declared={declared_total} but actual={actual_total}",
        )
    if declared_empty != actual_empty:
        report.error(
            "A:metrics-drift",
            f"empty_containers declared={declared_empty} but actual={actual_empty}",
        )
    if declared_hp != actual_enemy_hp:
        report.error(
            "A:metrics-drift",
            f"total_enemy_hp declared={declared_hp} but actual={actual_enemy_hp}",
        )

    return {
        "total_containers": actual_total,
        "empty_containers": actual_empty,
        "total_enemy_hp": actual_enemy_hp,
        "overall_emptiness_percent": round(
            100 * actual_empty / actual_total, 1
        ) if actual_total else 0.0,
    }


# ---------------------------------------------------------------------------
# B. Tier-ceiling violations
# ---------------------------------------------------------------------------
def check_tier_ceilings(level, zone_map, report):
    ceilings = level.get("survival_horror_systems", {}).get(
        "tier_ceiling_by_zone", {}
    )
    if not ceilings:
        report.note("B:tier-ceiling", "No tier_ceiling_by_zone defined; skipped.")
        return

    unmapped_rooms = set()

    for room in level.get("spatial_nodes", []):
        room_id = room["room_id"]
        zone = zone_map.get(room_id)
        if zone is None:
            unmapped_rooms.add(room_id)
            continue
        max_tier = ceilings.get(zone, {}).get("max_tier")
        if max_tier is None:
            continue

        for e in room.get("functional_entities", []):
            items = e.get("items") or ([e["item"]] if "item" in e else [])
            for it in items:
                tier = it.get("tier")
                if tier is not None and tier > max_tier:
                    report.error(
                        "B:tier-ceiling",
                        f"{room_id} (zone={zone}, max_tier={max_tier}): "
                        f"{e.get('entity_id')} has item '{it.get('item_id')}' "
                        f"at tier {tier}",
                    )

    if unmapped_rooms:
        report.warn(
            "B:tier-ceiling",
            f"{len(unmapped_rooms)} room(s) not found in zone map, skipped: "
            f"{sorted(unmapped_rooms)}. Tier-ceiling checks are incomplete "
            f"for these rooms.",
        )


# ---------------------------------------------------------------------------
# C. Orphaned rooms (no directed path to/from hub)
# ---------------------------------------------------------------------------
def check_orphaned_rooms(level, report):
    sh = level.get("survival_horror_systems", {})
    hub = sh.get("hub_node_id")
    if not hub:
        report.note("C:orphan-rooms", "No hub_node_id defined; skipped.")
        return

    all_rooms = {room["room_id"] for room in level.get("spatial_nodes", [])}
    if hub not in all_rooms:
        report.error(
            "C:orphan-rooms",
            f"hub_node_id '{hub}' does not match any room_id in spatial_nodes.",
        )
        return

    # Build directed adjacency (forward) and reverse adjacency (for "path
    # back to hub" check).
    forward = defaultdict(set)
    reverse = defaultdict(set)
    for room in level.get("spatial_nodes", []):
        rid = room["room_id"]
        for c in room.get("connections", []):
            target = c.get("connected_to")
            if target:
                forward[rid].add(target)
                reverse[target].add(rid)

    def bfs(start, graph):
        seen = {start}
        q = deque([start])
        while q:
            cur = q.popleft()
            for nxt in graph.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        return seen

    reachable_from_hub = bfs(hub, forward)
    can_reach_hub = bfs(hub, reverse)

    unreachable_from_hub = all_rooms - reachable_from_hub
    cannot_return_to_hub = all_rooms - can_reach_hub

    for r in sorted(unreachable_from_hub):
        report.error(
            "C:orphan-rooms",
            f"'{r}' is not reachable from hub '{hub}' (no forward path in).",
        )
    for r in sorted(cannot_return_to_hub):
        report.error(
            "C:orphan-rooms",
            f"'{r}' has no directed path back to hub '{hub}' "
            f"(may be a dead end or one-way trap).",
        )


# ---------------------------------------------------------------------------
# D. Dangling puzzle/loop requirements
# ---------------------------------------------------------------------------
def check_dangling_requirements(level, report):
    sh = level.get("survival_horror_systems", {})

    required_ids = set()
    sources = defaultdict(list)

    for pg in sh.get("puzzle_gates", []):
        rid = pg.get("key_item_required")
        if rid:
            required_ids.add(rid)
            sources[rid].append(f"puzzle_gate:{pg.get('puzzle_id')}")

    for loop in sh.get("backtracking_loops", []):
        rid = loop.get("trigger_item")
        if rid:
            required_ids.add(rid)
            sources[rid].append(f"backtracking_loop:{loop.get('loop_id')}")

    for gated in sh.get("gated_single_entry_rooms", []):
        rid = gated.get("trigger_item")
        if rid:
            required_ids.add(rid)
            sources[rid].append(
                f"gated_single_entry_room:{gated.get('room_id')}"
            )

    placed_ids = set()
    for room in level.get("spatial_nodes", []):
        for e in room.get("functional_entities", []):
            for it in e.get("items", []):
                placed_ids.add(it.get("item_id"))
            if "item" in e:
                placed_ids.add(e["item"].get("item_id"))

    missing = required_ids - placed_ids
    for m in sorted(missing):
        report.error(
            "D:dangling-requirement",
            f"'{m}' is required by {', '.join(sources[m])} but is never "
            f"placed as a pickup anywhere in spatial_nodes.",
        )


# ---------------------------------------------------------------------------
# E. Damage potential (informational, requires item_tiers.json)
# ---------------------------------------------------------------------------
AMMO_FOR_WEAPON = {
    "weapon_handgun": "ammo_handgun",
    "weapon_shotgun": "ammo_shotgun_shells",
    "weapon_magnum": "ammo_magnum",
}


def check_damage_potential(level, item_tiers, report):
    if item_tiers is None:
        report.note(
            "E:damage-potential",
            "--item-tiers not supplied; damage-potential check skipped.",
        )
        return None

    tier_lookup = {it["item_id"]: it for it in item_tiers.get("items", [])}

    placed = []
    for room in level.get("spatial_nodes", []):
        for e in room.get("functional_entities", []):
            placed.extend(e.get("items", []))
            if "item" in e:
                placed.append(e["item"])

    ammo_totals = defaultdict(int)
    weapon_instances = []
    for it in placed:
        meta = tier_lookup.get(it.get("item_id"))
        if not meta:
            continue
        if meta.get("category") == "ammo":
            ammo_totals[it["item_id"]] += it.get("quantity", 0)
        if meta.get("category") == "weapon" and "damage" in meta:
            weapon_instances.append((it["item_id"], meta["damage"]))

    total_damage_potential = 0
    for wid, dmg in weapon_instances:
        ammo_id = AMMO_FOR_WEAPON.get(wid)
        qty = ammo_totals.get(ammo_id, 0) if ammo_id else 0
        total_damage_potential += dmg * qty

    actual_enemy_hp = sum(
        enemy.get("health", 0)
        for room in level.get("spatial_nodes", [])
        for enemy in room.get("enemies", [])
    )
    ratio = (
        round(total_damage_potential / actual_enemy_hp, 2)
        if actual_enemy_hp
        else None
    )

    report.note(
        "E:damage-potential",
        f"total_loot_damage_potential={total_damage_potential}, "
        f"health_ammo_supply_ratio={ratio} "
        f"(damage potential ÷ total_enemy_hp={actual_enemy_hp})",
    )

    if ratio is not None and ratio > 3.0:
        report.warn(
            "E:damage-potential",
            f"health_ammo_supply_ratio={ratio} is high (player can defeat "
            f"all enemies ~{ratio}x over with placed ammo). Consider this "
            f"against your intended tension curve.",
        )

    return {
        "total_loot_damage_potential": total_damage_potential,
        "health_ammo_supply_ratio": ratio,
    }


# ---------------------------------------------------------------------------
# --write-metrics: regenerate declared metrics in place from real data
# ---------------------------------------------------------------------------
def write_metrics(level, zone_map, computed, damage_computed, out_path):
    lbm = level.setdefault("level_balance_metrics", {})
    lbm["total_containers"] = computed["total_containers"]
    lbm["empty_containers"] = computed["empty_containers"]
    lbm["total_enemy_hp"] = computed["total_enemy_hp"]
    lbm["overall_emptiness_percent"] = f"{computed['overall_emptiness_percent']}%"

    if damage_computed:
        lbm["total_loot_damage_potential"] = damage_computed[
            "total_loot_damage_potential"
        ]
        lbm["health_ammo_supply_ratio"] = damage_computed["health_ammo_supply_ratio"]

    # Per-zone container emptiness
    zone_containers = defaultdict(int)
    zone_empty = defaultdict(int)
    for room_id, e, is_empty in collect_containers(level):
        zone = zone_map.get(room_id)
        if not zone:
            continue
        zone_containers[zone] += 1
        if is_empty:
            zone_empty[zone] += 1

    tuning = level.get("survival_horror_systems", {}).get(
        "container_emptiness_tuning"
    )
    if tuning is not None:
        for zone in zone_containers:
            c = zone_containers[zone]
            e = zone_empty[zone]
            tuning[f"{zone}_ratio"] = round(e / c, 4) if c else 0.0
        tuning["overall_emptiness_percent"] = (
            f"{computed['overall_emptiness_percent']}%"
        )

    with open(out_path, "w") as f:
        json.dump(level, f, indent=2)
    print(f"\n📝 Regenerated metrics written to: {out_path}")


def print_stats(level):
    """Plain overview of the level's contents — no pass/fail judgment,
    just a sanity-check snapshot after an edit."""
    rooms = level.get("spatial_nodes", [])
    total_containers = 0
    empty_containers = 0
    total_enemies = 0
    total_enemy_hp = 0
    puzzle_gates = level.get("survival_horror_systems", {}).get(
        "puzzle_gates", []
    )
    loops = level.get("survival_horror_systems", {}).get(
        "backtracking_loops", []
    )

    for room in rooms:
        for e in room.get("functional_entities", []):
            if e.get("type") == "Container":
                total_containers += 1
                if not e.get("items"):
                    empty_containers += 1
        for enemy in room.get("enemies", []):
            total_enemies += 1
            total_enemy_hp += enemy.get("health", 0)

    print("=" * 72)
    print(f"LEVEL STATS: {level.get('scenario_title', '(untitled)')}")
    print("=" * 72)
    print(f"\n  Rooms:              {len(rooms)}")
    print(f"  Containers:         {total_containers} "
          f"({empty_containers} empty)")
    print(f"  Enemies:            {total_enemies} "
          f"(total HP: {total_enemy_hp})")
    print(f"  Puzzle gates:       {len(puzzle_gates)}")
    print(f"  Backtracking loops: {len(loops)}")
    print("\n  (This is just a snapshot — run without --stats for a real "
          "problem check.)")
    print("=" * 72)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="validate_level.py",
        description=(
            "Checks a level design JSON file for problems (broken puzzles, "
            "mislabeled numbers, unreachable rooms) and explains findings "
            "in plain language. New to this tool? Run with --guide first."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  python3 validate_level.py my_level.json\n"
            "      Basic check.\n\n"
            "  python3 validate_level.py my_level.json --item-tiers item_tiers.json\n"
            "      Also checks item tiers and ammo balance.\n\n"
            "  python3 validate_level.py my_level.json --summary\n"
            "      Quick one-line-per-category view.\n\n"
            "  python3 validate_level.py my_level.json --stats\n"
            "      Just show me numbers, no pass/fail judgment.\n\n"
            "  python3 validate_level.py my_level.json --write-metrics\n"
            "      Auto-fix the summary numbers, save as a new file.\n\n"
            "  python3 validate_level.py --explain D\n"
            "      Explain what a 'D:dangling-requirement' finding means.\n\n"
            "  python3 validate_level.py --guide\n"
            "      Full plain-language walkthrough of this whole tool.\n"
        ),
    )
    parser.add_argument(
        "level_file", nargs="?", default=None,
        help="The level JSON file to check.",
    )
    parser.add_argument(
        "--item-tiers", default=None,
        help="Path to your item catalog (e.g. item_tiers.json). Enables "
             "the tier-ceiling and ammo-balance checks.",
    )
    parser.add_argument(
        "--zone-map", default=None,
        help="Optional override file mapping room IDs to zone names, if "
             "the built-in default doesn't match your level.",
    )
    parser.add_argument(
        "--write-metrics", action="store_true",
        help="Recalculate the summary numbers from the real level data and "
             "save a corrected copy (never overwrites your original file).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="For automated tools/CI only: exit with an error status if "
             "any problem is found. Doesn't change what's printed.",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a condensed one-line-per-category view instead of the "
             "full detailed report.",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Just print an overview of the level's contents (room/item/"
             "enemy counts) -- no pass/fail checking.",
    )
    parser.add_argument(
        "--guide", action="store_true",
        help="Print a full plain-language walkthrough of every term and "
             "command this tool has, with examples. Start here if you're "
             "new.",
    )
    parser.add_argument(
        "--glossary", action="store_true",
        help="Print definitions for every term and check code this tool "
             "uses.",
    )
    parser.add_argument(
        "--explain", metavar="CODE", default=None,
        help="Explain one specific check code you saw in a report, e.g. "
             "--explain D",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Commands that don't need a level file at all.
    if args.guide:
        print_guide()
        sys.exit(0)
    if args.glossary:
        print_glossary()
        sys.exit(0)
    if args.explain:
        print_explain(args.explain)
        sys.exit(0)

    if not args.level_file:
        parser.error(
            "a level file is required (or run --guide / --glossary / "
            "--explain CODE, which don't need one)."
        )

    try:
        with open(args.level_file) as f:
            level = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Could not read '{args.level_file}' — it isn't valid JSON.")
        print(f"   Details: {e}")
        print(
            "   This usually means a typo like a missing comma or bracket "
            "was introduced in a manual edit. Check the area around line "
            f"{e.lineno} of the file."
        )
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ File not found: '{args.level_file}'")
        sys.exit(1)

    if args.stats:
        print_stats(level)
        sys.exit(0)

    item_tiers = None
    if args.item_tiers:
        with open(args.item_tiers) as f:
            item_tiers = json.load(f)

    zone_map = get_zone_map(args)
    report = Report()

    computed = check_metrics_drift(level, report)
    check_tier_ceilings(level, zone_map, report)
    check_orphaned_rooms(level, report)
    check_dangling_requirements(level, report)
    damage_computed = check_damage_potential(level, item_tiers, report)

    if args.summary:
        print(report.render_summary())
    else:
        print(report.render())

    if args.write_metrics:
        out_path = args.level_file.rsplit(".json", 1)[0] + ".validated.json"
        write_metrics(level, zone_map, computed, damage_computed, out_path)

    if args.strict and report.has_problems():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
