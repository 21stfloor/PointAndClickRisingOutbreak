---
name: point-and-click-prototype
description: >-
  Generates a standalone, zero-dependency, single-file HTML5/JavaScript interactive point-and-click browser game from completed concept art images, story.json, and threat configurations for rapid playtesting of camera-dependent hotspot visibility, 5-slot inventory item swapping, animated zombie threat scaling (zombie_transparent.png / zombie_attack_transparent.png), safe room NPC interactions, and room navigation pacing.
---

# SKILL: Generate Playable Point-and-Click Prototype (with Camera-Gated Hotspots & Threat Combat)

## Description
Generates a complete, zero-dependency, single-file HTML5/JavaScript interactive point-and-click browser game. It maps generated concept art backgrounds to room IDs, creates clickable hotspots for doors, key items, furniture containers, and active/lurking threats (Zombies/Bosses), providing an instant way to playtest progression pacing, camera exploration, inventory swapping, and survival horror tension in a web browser.

## Inputs Required
1. Level Structure JSON (`structural_level_design.json` / `structural level design.json`)
2. Story & Level JSON (`story.json` / `sample_game.json` containing item budgets, enemy spawn nodes, and camera angle lists)
3. Reference Item Database (`skills/reference/item_tiers.json`)
4. Concept art background images for each camera angle (including `zombie_transparent.png` and `zombie_attack_transparent.png` assets).

## System Instructions

### Step 1: Camera-Gated Hotspot Visibility Architecture
- Each room contains one or more camera angles (`camera_id` / camera labels e.g., East Elevation, West Elevation, Desk Close-Up).
- **Camera-Specific Interactables:** Every clickable hotspot (door, item, container, console) MUST be bound to a specific `camera_id` or active view angle.
- Hotspots are rendered and interactive ONLY when the player has selected and is actively viewing that specific camera perspective. This forces the player to switch camera views to thoroughly inspect the room and discover hidden interactables.

### Step 2: Inventory System (5-Slot Limit, Equip, Swapping & Cancellation)
1. **Strict 5-Slot Capacity:** Player inventory is capped at exactly 5 slots.
2. **Item Use & Equip (No Discarding):**
   - Players can equip weapons/tools or consume healing items (Herbs, Bandages, First Aid Spray).
   - Items cannot be discarded onto the floor.
3. **Item Swapping Logic:**
   - When picking up a new item while the inventory is at capacity (5 items):
     - The mouse cursor transforms into a **Hand Icon** to indicate picking/swapping mode.
     - The player must click an existing item in their 5-slot inventory to swap and replace it with the newly discovered item.
   - **Picking Cancellation:** The player can cancel the picking/swapping state at any time via ESC, right-click, or a "Cancel Pick" button.
   - **Zombie Combat Interrupt:** If a zombie attacks the player while in picking/swapping mode, the picking action is automatically interrupted and cancelled!

### Step 3: Zombie Threat Animations & Combat Mechanics
1. **Animated Approach (`zombie_transparent.png`):**
   - When a zombie threat is active in a room, render `zombie_transparent.png` overlaid on the room viewport.
   - Scale the zombie image up gradually over time to visually represent the zombie creeping/advancing closer to the player.
2. **Attacking Frame (`zombie_attack_transparent.png`):**
   - When the zombie reaches attack range or strikes, swap the sprite to `zombie_attack_transparent.png` to show the attack frame.
   - Inflict damage on player HP and trigger a camera shake/blood flash, then revert back to default state or retreat.
   - **Interruption:** Any active item picking or inventory swapping process is immediately interrupted and cancelled when a zombie attack hits.
3. **Weapon Defense:**
   - Equipping weapons (Handgun, Shotgun, Magnum) and spending ammo lets the player shoot approaching zombies before they reach attack range.

### Step 4: NPC Placement & Safe Room Rules
1. **No NPCs in Hallways:** NPCs are strictly prohibited in transit hallways or corridors.
2. **No NPCs in Threat Rooms:** NPCs must NEVER spawn in rooms containing active or lurking zombies.
3. **Safe Room Only Placement:** NPCs are placed strictly inside designated Safe Rooms (rooms with zero enemy spawns).
4. **NPC Interactions & Item Trades:** Clicking an NPC in a safe room opens dialogue and trade options (e.g. trading specific key items for quest progression or rewards).

### Step 5: Game State & Victory Conditions
- Tracks `playerHP` (100 HP max), 5-slot `inventory`, `ammo`, `currentRoom`, `activeCameraIndex`, and cleared threat states.
- **Loss Condition:** `playerHP <= 0` triggers Game Over with a Restart option.
- **Win Condition:** Reaching the final apex room (`RM_05_LOADING_DOCK`), restoring generator power, opening the motorized shutter, and boarding the escape boat triggers Scenario Complete.

### Step 6: Execution Output Format
When instructed to output a prototype, produce the complete, self-contained HTML/CSS/JS file ready to be saved as `playtest_prototype.html` and opened directly in any browser.
