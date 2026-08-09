---
name: point-and-click-prototype
description: >-
  Generates a standalone, zero-dependency, single-file HTML5/JavaScript interactive point-and-click browser game from completed concept art images and a story.json file for rapid playtesting of progression pacing, item looting, and room navigation.
---

# SKILL: Generate Playable Point-and-Click Prototype

## Description
Generates a complete, zero-dependency, single-file HTML5/JavaScript interactive point-and-click browser game. It maps generated concept art backgrounds to room IDs, creates clickable hotspots for doors, key items, and furniture containers, and provides an instant way to playtest progression pacing.

## Inputs Required
1. Story & Level JSON (`story.json` generated from Skill 1)
2. Path or filenames of concept art images for each room background.

## System Instructions

### Step 1: HTML/CSS/JS Architecture
- Generate a single self-contained `index.html` file containing HTML5 Canvas / Overlay DIVs, CSS styling, and Vanilla JavaScript logic.
- Include a visual UI with:
  - Background image viewport representing the current `room_id`.
  - Inventory bar showing held items (Keys, Ammo, Weapons, Heals).
  - Narrative/Action Log text box at the bottom.
  - Interactive clickable Hotspot bounding boxes over doors and furniture.

### Step 2: Gameplay Logic Implementation
1. **Container Interaction:** Clicking a furniture container inspects it. If items exist in `story.json`, add them to player inventory and log text (e.g., "Found 6x Handgun Ammo in Desk").
2. **Door Navigation & Gating:** Clicking a door transition checks if the required key/event in `progression_step` is completed. If locked, display "Door is locked."
3. **Progression Test:** Verify that the player can start in Room 1, loot items, unlock gates sequentially, and reach the final apex room without soft-locking.

### Step 3: Execution Output
Produce the full HTML/JS code block ready to be saved as `playtest_prototype.html` and opened directly in any web browser.
