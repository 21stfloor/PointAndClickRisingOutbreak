---
name: level-design-modifier
description: >-
  Modifies and updates a structural level design JSON file (e.g., structural level design.json) based on user playtesting feedback, pacing adjustments, room connection updates, camera angle reconfigurations, functional entity relocations, and safe-room NPC placement compliance.
---

# SKILL: Structural Level Design Modifier & Updater

## Description
Takes playtest feedback, pacing notes, or user prompt suggestions and modifies a level structure JSON (`structural level design.json` / `story.json`). It updates spatial room dimensions, camera angles, container item budgets, door connection vectors, functional entity positions, and NPC placement rules while maintaining structural level design integrity.

## Inputs Required
1. Target Level Structure JSON (`story/Amrathshear/scenarios/scenario1/structural level design.json` or scenario JSON).
2. Playtest feedback or prompt adjustment instructions (e.g., *"Move the principal key item to Lab A"*, *"Convert Room 3 into a Safe Room with an NPC"*, *"Add camera angles for hidden containers"*).

## System Instructions

### Step 1: Read and Inspect Target Level JSON
- Read the existing `structural level design.json` or scenario level file.
- Inspect `spatial_nodes`, `functional_entities`, `connections`, `fixed_cameras`, `enemies`, and `level_balance_summary`.

### Step 2: Apply Requested Level Adjustments
1. **Spatial Node & Room Dimensions:**
   - Update room `dimensions` (`width_x`, `length_y`, `height_z`) and `center_position` if requested.
2. **Door Connection Vectors:**
   - Ensure bidirectional connection symmetry (if Room A connects to Room B via exit vector, verify Room B has a corresponding connection back to Room A).
3. **Camera Angle & Hotspot Reconfigurations:**
   - Add, rename, or re-align `fixed_cameras` (`camera_id`, `position`, `rotation_euler`).
   - Assign camera-specific visibility mappings to functional entities and doors.
4. **NPC & Safe Room Compliance Rules:**
   - **No Hallway NPCs:** NPCs (`NPC_Interaction_Node`) must never be placed in transition corridors or hallways.
   - **No Threat Room NPCs:** NPCs must NEVER be placed in rooms containing active or lurking enemy spawns.
   - **Safe Room Validation:** If an NPC is added or moved to a room, automatically ensure that room is designated a Safe Room by clearing enemy spawn nodes from that node.
5. **Item Scarcity & Container Balance:**
   - Adjust container counts, empty container ratios, and item tiers based on playtest feedback.

### Step 3: Validation & Output
- Validate JSON schema syntax and structure.
- Save the updated JSON back to `story/Amrathshear/scenarios/scenario1/structural level design.json` (or the target scenario file path).
- Report a summary of changes made (rooms updated, connections modified, cameras re-aligned, and safe room NPC status).
