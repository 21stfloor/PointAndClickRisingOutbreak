---
name: point-and-click-prototype
description: >-
  Generates a standalone, zero-dependency, single-file HTML5/JavaScript interactive point-and-click browser game from completed concept art images, story.json, and threat configurations for rapid playtesting of camera-dependent hotspot visibility, 5-slot inventory item swapping (with item icons and container exchange), readable document files and lore memos (Document_Item_Node), persistent unlocked doors, targeted item usage with dropdown selection, weapon equipping, diegetic 2D floor map canvas with color-coded doors (red locked, green unlocked), animated zombie threat scaling (zombie_transparent.png / zombie_attack_transparent.png), direct tap combat with blood splash sprites & gunshot audio, safe room NPC interactions, and room navigation pacing.
---

# SKILL: Generate Playable Point-and-Click Prototype (with Camera-Gated Hotspots & Threat Combat)

## Description
Generates a complete, zero-dependency, single-file HTML5/JavaScript interactive point-and-click browser game. It maps generated concept art backgrounds to room IDs, creates clickable hotspots for doors, key items, readable document files, furniture containers, and active/lurking threats (Zombies/Bosses), providing an instant way to playtest progression pacing, camera exploration, inventory swapping, targeted item usage, diegetic 2D floor map navigation, and survival horror tension in a web browser.

## Inputs Required
1. Level Structure JSON (`structural_level_design.json` / `structural level design.json` / `sample_game.json`)
2. Concept art background images for each camera angle (including `zombie_transparent.png` and `zombie_attack_transparent.png` assets).

## System Instructions

### Step 1: Camera-Gated Hotspot Visibility Architecture
- Each room contains one or more camera angles (`camera_id` / camera labels e.g., East Elevation, West Elevation, Desk Close-Up).
- **Camera-Specific Interactables:** Every clickable hotspot (door, item, document, container, console) MUST be bound to a specific `camera_id` or active view angle.
- Hotspots are rendered and interactive ONLY when the player has selected and is actively viewing that specific camera perspective. This forces the player to switch camera views to thoroughly inspect the room and discover hidden interactables.

### Step 2: Inventory System (5-Slot Limit, Icons, Equip, Targeted Use & Container Drop)
1. **Strict 5-Slot Capacity:** Player inventory is capped at exactly 5 slots for physical items.
2. **Item Icons:** Every item name in UI slots, swap banners, tooltips, and action logs MUST display its item emoji icon (e.g. `🔑 Rusted Padlock Key`, `🔫 9mm Handgun`, `🌿 Green Herb`).
3. **Weapon Equipping:** Weapons (Handgun, Shotgun, Magnum) must be explicitly equipped from inventory before they can be used in combat. Tracks `state.equippedWeaponId`.
4. **Targeted Item Usage & Dropdown Selection:**
   - Key items and tools (keys, keycards, lockpicks, fuses, chemical agents) must be used on specific targets.
   - When examining a key item in inventory, render a **Target Dropdown Menu** listing all visible interactables/doors in the active camera view.
   - Clicking "🔑 Use Item on Target":
     - If the item matches the target's `required_key` (case-insensitive evaluation), it permanently unlocks/activates the target, logs a success event (`🔓 SUCCESS: Used [🔑 Key] on [Door]!`), and removes single-use items.
     - If the item does not match the target, it logs an explicit failure event (`❌ FAILED: Cannot use [🔑 Key] on [Desk]. It has no effect!`).
5. **Persistent Unlocked Doors & Explicit Key Usage:**
   - Doors requiring keys CANNOT be navigated by clicking directly on them, even if the key is held in inventory.
   - The player MUST inspect the key item in their inventory and select "Use Item on Target" targeting the door to unlock it.
   - Unlocked doors are saved in `state.unlockedDoors = new Set()`. Once explicitly unlocked via inventory item usage, doors stay permanently unlocked and can be traversed freely.
6. **Item Swapping & World Container Exchange:**
   - When picking up a new item while the inventory is at capacity (5 items):
     - The mouse cursor transforms into a **Hand Icon** to indicate picking/swapping mode.
     - Displays swapping banner with item icon: `✋ Select an item in 5-slot inventory to SWAP with [🔑 Rusted Padlock Key]`.
     - The player selects an existing item in their 5-slot inventory to swap out.
     - **Container/Ground Exchange Rule:** The swapped-out inventory item replaces the picked-up item inside its original container or ground hotspot! The old item is NOT lost; it remains stored in the container/hotspot so the player can return and pick it up again later.
   - **Picking Cancellation:** The player can cancel picking/swapping via ESC, right-click, or a "Cancel Pick" button.
   - **Zombie Combat Interrupt:** If a zombie attacks the player while in picking/swapping mode, picking is automatically cancelled!
   - **Screen / Camera View Change Interrupt:** If the player changes screens, switches camera perspectives (`cam-btn`), or navigates to another room (`changeRoom`) while in picking/swapping mode (`state.isSwapping`), item picking is automatically cancelled (`cancelItemSwapping()`)!

### Step 3: Readable Document Files, Notes & Lore Memos
1. **Document Node Architecture (`Document_Item_Node` / `type: "document"`):**
   - Documents represent collectible/readable lore notes, security logs, synthesis reports, and puzzle combination clues found in the level.
   - Hotspot definition includes `id`, `type: "document"`, `name` / `title`, `content` (full readable text narrative), and `icon` (e.g. `📜`, `📄`, `📝`).
2. **Document Reader Modal Overlay (`documentModal`):**
   - Clicking a document hotspot or inspecting a document item opens a dedicated **Document Reader Modal** (`documentModal`).
   - Renders a stylized parchment / computer terminal note card displaying document title, timestamp, icon, and full readable text narrative.
   - Logs document reading to action history: `📜 Read Document: [Security Guard Duty Memo]`.

### Step 4: Diegetic 2D Floor Map Canvas & Map Item Requirement
1. **Map Item Required:**
   - Opening the tactical map (`mapModal`) requires that the player has looted/picked up the layout map item (`ITEM_LAYOUT_MAP` / `item_map`) at least once during play (`state.hasMapPickedUp`).
   - If the map item has not been retrieved yet, display a notice: `🗺️ Layout Map Not Found! Loot the School Layout Map from the Main Vestibule Kiosk Desk first!`.
2. **2D Canvas Map Drawing:**
   - Draw an actual 2D floor map on `<canvas id="mapCanvas">` using the spatial bounding boxes (`dimensions.width_x`, `length_y`, `center_position.x`, `center_position.y`) from the level JSON.
3. **Thick Line Color-Coded Doors:**
   - Render door connections between rooms as thick (6px) lines on the map canvas:
     - 🔴 **Red Thick Line (`#ff4d4d`)**: Locked door (requires key item).
     - 🟢 **Green Thick Line (`#2ec4b6`)**: Unlocked door (traversable).
     - 🟡 **Gold Box (`#ffb703`)**: Active player room position.

### Step 5: Camera-Gated Zombie Threats, Direct Tap Combat & Blood Splash Audio
1. **Single Camera Angle Binding:**
   - Zombies and enemies are bound to exactly ONE specific camera angle (`camIndex`) in a room.
   - The zombie sprite overlay appears and advances towards attack ONLY when the player is actively viewing its designated camera angle. Switching to another camera angle in the room hides the zombie from the viewport.
2. **Left-Right Swaying & Scale Persistence:**
   - As the zombie approaches, `state.zombieScale` increases from 0.3 up to 1.0 (full proximity).
   - While moving close, the zombie sways horizontally left and right (`zombieOffsetX`) in a sinuous motion bounded comfortably within viewport boundaries.
   - **Persistent Proximity Scale:** Once the zombie reaches full scale (1.0), it DOES NOT reset back to small scale (0.3). It remains scaled up at close proximity and strikes the player repeatedly on a **cooldown timer** (e.g. every 1.8 seconds) as long as it lives!
3. **Direct Tap Canvas Combat:**
   - Combat requires the player to **tap/click directly on the zombie sprite overlay** on the viewport canvas!
   - **Gunshot Audio FX:** Firing a weapon triggers an authentic synthesized gunshot sound effect using lowpass white-noise explosive buffers and rapid pitch drops (`playSound('shoot')`).
   - **Blood Splash Sprite FX:**
     - Scoring a direct hit spawns an animated **Blood Splash Sprite Overlay** (`state.bloodSplats`) right at the hit coordinates `(mx, my)`.
     - Draws expanding dark gore cores, radial blood droplet spray particles, and floating `💥 BLOOD HIT!` impact text that fades out smoothly over 650ms.
   - **HIT:** Clicking on the zombie sprite with an equipped weapon consumes 1 ammo, deals damage to the zombie (`enemy.hp -= damage`), applies a minor scale knockback (`state.zombieScale -= 0.25`), and logs a direct hit event (`🎯 DIRECT HIT! Fired [Weapon] at [Zombie] for [DMG] DMG!`).
   - **MISS:** Clicking off-target on the canvas background while a weapon is equipped STILL consumes 1 ammo, plays the gunshot sound, and logs a missed shot event (`❌ MISSED! Fired [Weapon] off-target into background wall! 1 ammo wasted!`).
4. **Attacking Frame & Interruption:**
   - When striking, swap the sprite to `zombie_attack_transparent.png`, deal damage to player HP, and trigger blood screen flash.
   - **Interruption:** Any active item picking or inventory swapping process is immediately interrupted and cancelled when a zombie attack hits.

### Step 6: Safe Room & NPC Rules
1. **No NPCs in Hallways:** NPCs are strictly prohibited in transit hallways or corridors.
2. **No NPCs in Threat Rooms:** NPCs must NEVER spawn in rooms containing active or lurking zombies.
3. **Safe Room Only Placement:** NPCs are placed strictly inside designated Safe Rooms (rooms with zero enemy spawns).
4. **NPC Interactions & Item Trades:** Clicking an NPC in a safe room opens dialogue and trade options.

### Step 7: Game State, Loss & Victory Conditions
- Tracks `playerHP` (100 HP max), 5-slot `inventory`, `equippedWeaponId`, `unlockedDoors`, `hasMapPickedUp`, `ammo`, `currentRoom`, `activeCameraIndex`, and cleared threat states.
- **Loss Condition:** `playerHP <= 0` immediately halts game loops and player interactions, displays the Game Over Modal overlay (`gameOverModal`) featuring death metrics (time survived, items looted, threats slain, sectors reached), and presents a '🔄 Restart Game' button.
- **Win Condition:** Reaching the final apex room (`RM_05_LOADING_DOCK`), restoring generator power, opening the motorized shutter, and boarding the escape boat triggers Scenario Complete.

### Step 8: Execution Output Format
When instructed to output a prototype, produce the complete, self-contained HTML/CSS/JS file ready to be saved as `playtest_prototype.html` and opened directly in any browser.
