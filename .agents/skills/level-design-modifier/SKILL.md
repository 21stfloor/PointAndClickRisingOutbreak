---
name: level-design-modifier
description: >-
  Modifies and updates a structural level design JSON file (e.g., sample_game6.json /
  "structural level design.json") based on user playtesting feedback, pacing
  adjustments, room connection updates, camera angle reconfigurations, functional
  entity relocations, and safe-room NPC placement compliance. Every edit is checked
  by the validate_level.py tool before being considered complete, and design-judgment
  calls (pacing, tension, scarcity) are grounded in the reference material under
  references/ rather than guessed.
---

# SKILL: Structural Level Design Modifier & Updater

## Description
Takes playtest feedback, pacing notes, or prompt-based adjustment instructions and
modifies a level structure JSON. It updates spatial room dimensions, camera angles,
container item budgets, door connection vectors, functional entity positions, puzzle
gates, backtracking loops, and NPC placement rules — then runs the standing
validation tool to confirm the edit didn't break anything, and recalculates the
summary metrics so they never silently drift out of sync with the actual content.

## Inputs Required
1. **Target level JSON** — e.g. `story/Amrathshear/scenarios/scenario1/structural_level_design.json`,
   or whatever scenario file the user points to. (Path is an example, not a hardcoded
   requirement — always operate on the file the user actually names.)
2. **Item catalog JSON** (e.g. `item_tiers.json`) — provides `tier`, `category`,
   `damage`, and `allowed_progression_steps` per item. Required for tier-ceiling and
   ammo-balance checks; if not supplied, ask the user for it or proceed with reduced
   validation and say so explicitly.
3. **Playtest feedback / prompt instructions** — e.g. *"Move the principal key item
   to Lab A,"* *"Convert Room 3 into a Safe Room with an NPC,"* *"This section feels
   too generous with ammo,"* *"The dock finale feels flat."*
4. **`validate_level.py`** — the standing validation CLI (kept alongside this skill,
   e.g. `.agents/skills/level-design-modifier/tools/validate_level.py`). This is not
   optional tooling — it is how every edit in Step 3 gets confirmed.
5. **`references/` transcripts** — design-theory source material (level pacing,
   tension design, resource scarcity, looping levels, etc.) used in Step 2b to turn
   qualitative feedback into concrete, defensible edits rather than guesses.

## System Instructions

### Step 1: Read, Inspect, and Baseline-Validate
- Read the target level JSON and, if available, the item catalog JSON.
- Inspect `spatial_nodes`, `functional_entities`, `connections`, `fixed_cameras`,
  `enemies`, `puzzle_gates`, `backtracking_loops`, `gated_single_entry_rooms`, and
  `level_balance_metrics`. (Note: the metrics block is `level_balance_metrics`, not
  `level_balance_summary` — use the real field name when reading/writing.)
- Run `validate_level.py <file> --item-tiers <catalog> --stats` first to get a clean
  snapshot of the current state before touching anything. If the baseline already
  has errors, tell the user before making new edits — don't let a pre-existing bug
  get attributed to the new change.

### Step 2: Apply Requested Level Adjustments

**2a. Structural / mechanical edits** (for direct, literal instructions):
1. **Spatial Node & Room Dimensions** — update `dimensions` (`width_x`, `length_y`,
   `height_z`) and `center_position` as requested.
2. **Door Connection Vectors** — for any *bidirectional* door type
   (`Standard_Interior_Door`, etc.), verify Room A → Room B has a matching B → A
   entry. For intentionally *one-way* types (`One_Way_Pass_Door`,
   `One_Way_Shortcut_Handle`, `Exit_Transition_Threshold`), do NOT add a reverse
   edge — that would silently convert a designed loop into a plain corridor. When
   unsure which category a door type falls into, check how it's used elsewhere in
   the same file before deciding.
3. **Camera Angle & Hotspot Reconfigurations** — add, rename, or re-align
   `fixed_cameras` (`camera_id`, `position`, `rotation_euler`); assign
   camera-specific visibility mappings to entities/doors as requested.
4. **NPC & Safe Room Compliance Rules:**
   - **No Hallway NPCs:** `NPC_Interaction_Node` must never be placed in transition
     corridors/hallways (`HW_*` rooms).
   - **No Threat Room NPCs:** NPCs must never be placed in a room with a non-empty
     `enemies` list.
   - **Safe Room Validation:** if an NPC is added/moved into a room, clear that
     room's `enemies` array so it qualifies as a Safe Room.
5. **Item Scarcity & Container Balance** — adjust container counts, item placement,
   and item tiers based on feedback.
6. **Cross-zone relocations** — if an edit moves an item (key, weapon, etc.) into a
   different zone (alley / school / docks, or whatever `tier_ceiling_by_zone`
   defines), check the item's `tier` against the destination zone's `max_tier`
   *before* placing it. If it would violate the ceiling, don't silently place it —
   flag the conflict to the user and ask whether to proceed anyway, swap for a
   lower-tier equivalent, or pick a different room.
7. **Puzzle/loop integrity on relocation or deletion** — before moving or removing
   any item, check whether its `item_id` appears as a `key_item_required` in
   `puzzle_gates` or a `trigger_item` in `backtracking_loops` /
   `gated_single_entry_rooms`. If so, either keep it placed somewhere reachable in
   the level or update/remove the referencing gate — don't leave a dangling
   requirement (this is exactly what `validate_level.py`'s `D:dangling-requirement`
   check exists to catch, but it's cheaper to avoid than to fix after the fact).

**2b. Judgment-call edits** (for qualitative/subjective feedback):
When feedback is qualitative rather than literal — *"feels too easy,"* *"boring,"*
*"too generous,"* *"this section drags"* — don't guess. Consult the transcripts in
`references/` for the relevant concept before deciding what to change, and briefly
cite which idea you're applying. Examples of how feedback maps to concrete edits:

| Feedback | Concept to check in references/ | Likely concrete edit |
|---|---|---|
| "Too much ammo / too easy" | resource scarcity, tension pacing | Lower `default_spawn_quantity`, raise a zone's `container_emptiness_tuning` ratio, re-run `validate_level.py --item-tiers` and check `health_ammo_supply_ratio` moved toward ~1.0–2.0 |
| "This room/hallway is boring" | environmental storytelling | Add diegetic props/clues to `functional_entities` rather than just more enemies |
| "Section feels like a slog / drags" | pacing & level length control | Look at puzzle-gate density on the critical path; consider trimming a gate or shortening backtracking distance |
| "Didn't feel like I was making progress" | looping levels, backtracking loops | Check whether a `backtracking_loops` shortcut is missing or too far from the triggering pickup |
| "This ladder/vertical section feels bad" | ladder design tradeoffs | Confirm it's not on a path traveled 2+ times, or convert to a different vertical solution |
| "Too tense with no relief" or "never scary" | tension balance / 5-step tension formula | Check spacing of `new_threat_spawns` and environmental state changes between rooms — look for missing "seed of doubt" or "diversion" beats |

### Step 3: Validate & Report (mandatory — do not skip)
1. **Update `level_balance_metrics` yourself as part of the edit**, don't leave it
   for the user to notice is stale. At minimum recompute `total_containers`,
   `empty_containers`, `overall_emptiness_percent`, `total_enemy_hp`, and (if item
   catalog available) `total_loot_damage_potential` / `health_ammo_supply_ratio`
   from the edited data — the same logic `validate_level.py --write-metrics`
   applies.
2. **Run the full check**:
   `validate_level.py <file> --item-tiers <catalog>`
   (or `--summary` for a quick pass). Do not report the task as done while this
   shows new errors that weren't present in the Step 1 baseline.
3. **If new errors appear**, fix them or explicitly flag to the user why they're
   being left (e.g., a deliberate design tradeoff) — never silently ship a level
   that regressed relative to baseline.
4. **Never overwrite the user's original file silently.** Save the edited result
   as a new file (e.g. `<original>.updated.json`) unless the user has explicitly
   said to edit in place, consistent with how `validate_level.py --write-metrics`
   itself never overwrites its input.
5. **Report a summary of changes** to the user in plain language: rooms updated,
   connections modified, cameras re-aligned, safe-room/NPC status, any cross-zone
   tier conflicts encountered, which reference concept (if any) informed a
   judgment-call edit, and the final validator output (clean, or explained
   warnings).
