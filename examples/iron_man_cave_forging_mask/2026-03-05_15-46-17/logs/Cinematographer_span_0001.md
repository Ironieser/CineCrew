# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 26897c809d8e48bb
- **Session ID**: dataset_iron_man_cave_forging_mask_2026-03-05_15-46-17
- **Timestamp**: 2026-03-05 15:48:39
- **Duration**: 39.95s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4521
- **completion_tokens**: 6052
- **total_tokens**: 10573

## Prompt Rendered

```
=== System ===
You are a Cinematographer / Director of Photography.
You are given a list of shots that have already been analysed for narrative intent.
Your single job: decide HOW to shoot each one — fill staging_layer.

You do NOT reinterpret the story. You do NOT change shot boundaries.
You only decide camera, lighting, entity placement, and constraints.

=========================================================
YOUR OUTPUT CONTRACT
=========================================================
Return a JSON object with one key "shots":
{
  "shots": [
    {
      "shot_id": "<same shot_id from input>",
      "staging_layer": { ... }
    },
    ...
  ]
}

The "shots" list MUST contain exactly the same shot_ids as the input,
in the same order. Do NOT add or remove shots.

staging_layer fields:
  - duration_seconds (float):
      Estimated shot duration. Must be > 1.0.
      Dialogue shots: ~2–4s per exchange. Action shots: 1.5–6s.
      Slow/atmospheric: up to 10s.

  - camera:
      - shot_scale: one of ["ECU","CU","MCU","MS","MLS","LS","ELS","OTS","POV"] or null
          ECU=extreme close-up, CU=close-up, MCU=medium close-up,
          MS=medium shot, MLS=medium long shot, LS=long shot,
          ELS=extreme long shot, OTS=over-the-shoulder, POV=point-of-view
      - angle: one of ["eye_level","low","high","dutch","overhead","undershot"] or null
      - movement: string or null
          Examples: "static", "slow_dolly_in", "pan_right", "handheld_follow",
          "crane_up", "rack_focus"

  - lighting (str|null):
      Lighting scheme label. Examples:
      "high-key daylight", "Rembrandt low-key", "silhouette backlight",
      "candlelight warm", "neon-lit night", "overcast soft fill"

  - environment_id (str|null):
      MUST be a loc_xxx ID from Asset Context. null if off-screen / unspecified.

  - entities: list of
      { asset_id, position (str|null), action_state (str|null) }
      - asset_id: MUST be char_xxx or prop_xxx from Asset Context.
      - position: compositional placement, e.g. "frame_left", "center_fg",
        "background_right", "seated_center"
      - action_state: what the entity is physically doing,
        e.g. "gesturing_forward", "leaning_back", "looking_offscreen_left"

  - consistency_constraints: list of strings
      Hard visual rules that Critic must verify, e.g.:
      - "Michael must wear dark suit throughout scene"
      - "Room lighting must remain low-key — no windows visible"
      Omit if none apply.

=========================================================
CINEMATOGRAPHY PRINCIPLES
=========================================================
- Match shot_scale to emotional intensity: intimate moments → CU/MCU,
  power dynamics → low/high angles, establishing context → LS/ELS.
- Vary shot scale across consecutive shots — avoid three MCUs in a row.
- Reserve camera movement for purposeful moments; default to "static".
- List only entities that are VISIBLE in this shot.
  If a character is heard but not seen, do NOT list them in entities.
- environment_id must match the setting described in narrative_action.

=========================================================
CRITICAL RULES
=========================================================
1. ALL asset_id / environment_id values MUST come from Asset Context.
   NEVER invent IDs.
2. Output shot_ids MUST exactly match the input shot_ids.
3. Do NOT output narrative_action, emotional_beat, or dialogue — those
   belong to narrative_layer and must not be repeated here.



--- [KNOWLEDGE: rules/common/naming.md] ---
# Naming Conventions (Common)


---

## Asset ID Format

- **Characters**: `char_{lowercase_name}` Example: `char_vito_corleone`
- **Locations**: `loc_{type}_{name}` Example: `loc_int_dons_office`
- **Props**: `prop_{name}` Example: `prop_cat`
- **Voices**: `voice_{character_name}` Example: `voice_bonasera`

## Shot ID Format

- **Original Shots**: `shot_{number}_{brief_description}` Example: `shot_01_vito_listens`
- **Decomposed Segments**: `{master_shot_id}_{segment_letter}` Example: `shot_01_a`, `shot_01_b`

## Multimodal Storage (Reference)

- **Visual References**: `assets/{asset_id}/visual/canonical.png`
- **Audio References**: `assets/{asset_id}/audio/voice_sample.wav`

**Mandatory**: All entity references MUST use Asset IDs (e.g. `char_vito_corleone`), never raw descriptions. Do NOT generate non-existent Asset IDs.

-----------------------------



--- [KNOWLEDGE: rules/common/anti_hallucination.md] ---
# Anti-Hallucination Mechanism (Common)


---

## Constraint Priority

1. **Location Lock** > LLM training data bias
2. **Era Lock** > Temporal feature inference
3. **Negative Constraints** > Model default associations

## Example

```
Script: "The Godfather"
❌ Wrong: LLM auto-associates "Sicily, olive groves, Mediterranean"
✅ Correct: Use ProjectSettings to force override "New York, NOT Italy/Sicily"
```

## Rules

- Do NOT invent locations/eras not implied by the script; use ProjectSettings (location_lock, era_lock, negative_constraints) when the script implies a known setting.
- ProjectSettings constraints MUST be respected in narrative_context and downstream shot prompts.

-----------------------------



🛡️ **CRITICAL CONSTRAINTS (MUST FOLLOW)**:
- **LOCATION LOCK**: Subterranean cave forge, undetermined locale — DO NOT infer or depict a specific country, culture, or fantasy realm (NOT medieval Europe, NOT feudal Japan, NOT Norse, NOT dwarven/Tolkien).
- **ERA LOCK**: Atemporal, era-agnostic underground workshop — no overt historical markers (NOT medieval, NOT steampunk, NOT cyberpunk, NOT futuristic sci‑fi).
- **FORBIDDEN ELEMENTS**: Medieval castle architecture, Viking/Norse runes, Celtic knotwork, Samurai armor, kabuto, katana, Torii gates, Gothic arches or stained glass, Art Deco motifs, Roman columns or Greek statues, Renaissance paintings, Fantasy dwarven halls (Moria style), Elven motifs, Steampunk gears and brass goggles, Cyberpunk neon and holograms, Futuristic sci‑fi technology, Electric lighting (bulbs, LEDs, fluorescents), Colored stage lighting, Windows, skylights, daylight shafts, Modern power tools (angle grinder, plasma cutter, electric welder), CNC machines, Computer screens or digital displays, Visible wiring and extension cords, Chrome or stainless steel polished finishes, Plastic components, Concrete or tiled walls/floors, White painted walls, Brand logos or modern signage, Safety signage and OSHA tape, Religious iconography, National flags or symbols, Text inscriptions in any language, Ornate jewelry inlays, gemstones, gold leaf, Stylized cultural masks (Kabuki, Oni, Venetian, tribal), Weapons beyond smithing tools, Firearms, Magical effects (glowing runes, enchanted light), Smoke machines or theatrical fog, Crowds or additional people; the blacksmith is alone, External light sources other than the forge fire, Countdown timers or digital clocks
- **STYLE OVERRIDES**:
  * color_palette: Firelit amber/orange highlights with deep charcoal and black shadows; gritty, high contrast.
  * architecture: Natural rough cave walls and stone; minimal, utilitarian forge fixtures only.
  * lighting: Single practical source: forge/fire glow; chiaroscuro; no fill, rim, overhead, or electric lights.
  * materials: Black iron/steel, raw stone, soot, ash; avoid polished or decorative finishes.
  * props: Manual smithing tools only (anvil, hammer, tongs); no powered equipment.
  * costume: Functional, neutral workwear (heavy apron, gloves); no cultural insignia or ornament.
  * set_dressing: Sparse, utilitarian; focus on labor and tools; no signage, logos, or decorative motifs.
  * mood: Tense, gritty, urgent; physical exertion emphasized by sparks and darkness.

⚠️ These constraints OVERRIDE any default associations in your training d
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_forge_fire_glows",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "MLS",
          "angle": "eye_level",
          "movement": "static"
        },
        "lighting": "single practical forge glow (chiaroscuro)",
        "environment_id": "loc_int_cave_forge",
        "entities": [
          {
            "asset_id": "char_blacksmith",
            "position": "center_midground",
            "action_state": "standing_over_anvil_looking_down"
          },
          {
            "asset_id": "prop_steel_anvil",
            "position": "center_fg",
            "action_state": "stationary"
          },
          {
            "asset_id": "prop_metal_mask",
            "position": "center_fg",
            "action_state": "glowing_red_hot_on_anvil"
          },
          {
            "asset_id": "prop_iron_hammer",
            "position": "frame_right",
            "action_state": "held_at_side"
          },
          {
            "asset_id": "prop_forge_fire",
            "position": "background_right",
            "action_state": "roaring"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Subterranean cave forge, undetermined locale — DO NOT infer or depict a specific country, culture, or fantasy realm (NOT medieval Europe, NOT feudal Japan, NOT Norse, NOT dwarven/Tolkien).",
          "ERA LOCK: Atemporal, era-agnostic underground workshop — no overt historical markers (NOT medieval, NOT steampunk, NOT cyberpunk, NOT futuristic sci‑fi).",
          "FORBIDDEN: Medieval castle architecture, Viking/Norse runes, Celtic knotwork, Samurai armor, kabuto, katana, Torii gates, Gothic arches or stained glass, Art Deco motifs, Roman columns or Greek statues, Renaissance paintings, Fantasy dwarven halls (Moria style), Elven motifs, Steampunk gears and brass goggles, Cyberpunk neon and holograms, Futuristic sci‑fi technology, Electric lighting (bulbs, LEDs, fluorescents), Colored stage lighting, Windows, skylights, daylight shafts, Modern power tools (angle grinder, plasma cutter, electric welder), CNC machines, Computer screens or digital displays, Visible wiring and extension cords, Chrome or stainless steel polished finishes, Plastic components, Concrete or tiled walls/floors, White painted walls, Brand logos or modern signage, Safety signage and OSHA tape, Religious iconography, National flags or symbols, Text inscriptions in any language, Ornate jewelry inlays, gemstones, gold leaf, Stylized cultural masks (Kabuki, Oni, Venetian, tribal), Weapons beyond smithing tools, Firearms, Magical effects (glowing runes, enchanted light), Smoke machines or theatrical fog, Crowds or additional people; the blacksmith is alone, External light sources other than the forge fire, Countdown timers or digital clocks",
          "COLOR_PALETTE: Firelit amber/orange highlights with deep charcoal and black shadows; gritty, high contrast.",
          "ARCHITECTURE: Natural rough cave walls and stone; minimal, utilitarian forge fixtures only.",
          "LIGHTING: Single practical source: forge/fire glow; chiaroscuro; no fill, rim, overhead, or electric lights.",
          "MATERIALS: Black iron/steel, raw stone, soot, ash; avoid polished or decorative finishes.",
          "PROPS: Manual smithing tools only (anvil, hammer, tongs); no powered equipment.",
          "COSTUME: Functional, neutral workwear (heavy apron, gloves); no cultural insignia or ornament.",
          "SET_DRESSING: Sparse, utilitarian; focus on labor and tools; no signage, logos, or decorative motifs.",
          "MOOD: Tense, gritty, urgent; physical exertion emphasized by sparks and darkness.",
          "Shot-specific: Forge fire must be visible in background and serve as the sole practical light source; no other light sources or windows.",
          "Shot-specific: Keep cave walls rough stone; maintain deep shadows around frame edges.",
          "Shot-specific: The blacksmith remains alone in frame."
        ]
      }
    },
    {
      "shot_id": "shot_02_hammer_raised_high",
      "staging_layer": {
        "duration_seconds": 3.2,
        "camera": {
          "shot_scale": "MCU",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "single practical forge glow (chiaroscuro)",
        "environment_id": "loc_int_cave_forge",
        "entities": [
          {
            "asset_id": "char_blacksmith",
            "position": "center_fg",
            "action_state": "heaving_hammer_raised_high_poised_to_strike"
          },
          {
            "asset_id": "prop_iron_hammer",
            "position": "upper_center_fg",
            "action_state": "raised_above_mask"
          },
          {
            "asset_id": "prop_metal_mask",
            "position": "center_fg",
            "action_state": "glowing_on_anvil"
          },
          {
            "asset_id": "prop_steel_anvil",
            "position": "center_fg",
            "action_state": "anchored_under_mask"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Subterranean cave forge, undetermined locale — DO NOT infer or depict a specific country, culture, or fantasy realm (NOT medieval Europe, NOT feudal Japan, NOT Norse, NOT dwarven/Tolkien).",
          "ERA LOCK: Atemporal, era-agnostic underground workshop — no overt historical markers (NOT medieval, NOT steampunk, NOT cyberpunk, NOT futuristic sci‑fi).",
          "FORBIDDEN: Medieval castle architecture, Viking/Norse runes, Celtic knotwork, Samurai armor, kabuto, katana, Torii gates, Gothic arches or stained glass, Art Deco motifs, Roman columns or Greek statues, Renaissance paintings, Fantasy dwarven halls (Moria style), Elven motifs, Steampunk gears and brass goggles, Cyberpunk neon and holograms, Futuristic sci‑fi technology, Electric lighting (bulbs, LEDs, fluorescents), Colored stage lighting, Windows, skylights, daylight shafts, Modern power tools (angle grinder, plasma cutter, electric welder), CNC machines, Computer screens or digital displays, Visible wiring and extension cords, Chrome or stainless steel polished finishes, Plastic components, Concrete or tiled walls/floors, White painted walls, Brand logos or modern signage, Safety signage and OSHA tape, Religious iconography, National flags or symbols, Text inscriptions in any language, Ornate jewelry inlays, gemstones, gold leaf, Stylized cultural masks (Kabuki, Oni, Venetian, tribal), Weapons beyond smithing tools, Firearms, Magical effects (glowing runes, enchanted light), Smoke machines or theatrical fog, Crowds or additional people; the blacksmith is alone, External light sources other than the forge fire, Countdown timers or digital clocks",
          "COLOR_PALETTE: Firelit amber/orange highlights with deep charcoal and black shadows; gritty, high contrast.",
          "ARCHITECTURE: Natural rough cave walls and stone; minimal, utilitarian forge fixtures only.",
          "LIGHTING: Single practical source: forge/fire glow; chiaroscuro; no fill, rim, overhead, or electric lights.",
          "MATERIALS: Black iron/steel, raw stone, soot, ash; avoid polished or decorative finishes.",
          "PROPS: Manual smithing tools only (anvil, hammer, tongs); no powered equipment.",
          "COSTUME: Functional, neutral workwear (heavy apron, gloves); no cultural insignia or ornament.",
          "SET_DRESSING: Sparse, utilitarian; focus on labor and tools; no signage, logos, or decorative motifs.",
          "MOOD: Tense, gritty, urgent; physical exertion emphasized by sparks and darkness.",
          "Shot-specific: The hammer must be clearly raised above the glowing mask blank; do NOT show the strike in this shot.",
          "Shot-specific: Keep the forge fire as off-frame light source; no additional fills or rims.",
          "Shot-specific: The blacksmith remains alone in frame."
        ]
      }
    },
    {
      "shot_id": "shot_03_sparks_violently_erupt",
      "staging_layer": {
        "duration_seconds": 2.4,
        "camera": {
          "shot_scale": "CU",
          "angle": "eye_level",
          "movement": "static"
        },
        "lighting": "single practical forge glow (chiaroscuro)",
        "environment_id": "loc_int_cave_forge",
        "entities": [
          {
            "asset_id": "char_blacksmith",
            "position": "frame_left",
            "action_state": "mid_strike_face_lit_by_sparks"
          },
          {
            "asset_id": "prop_iron_hammer",
            "position": "center_fg",
            "action_state": "impact_on_mask"
          },
          {
            "asset_id": "prop_metal_mask",
            "position": "center_fg",
            "action_state": "sparks_erupting_bright_orange"
          },
          {
            "asset_id": "prop_steel_anvil",
            "position": "center_fg",
            "action_state": "supporting_impact"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Subterranean cave forge, undetermined locale — DO NOT infer or depict a specific country, culture, or fantasy realm (NOT medieval Europe, NOT feudal Japan, NOT Norse, NOT dwarven/Tolkien).",
          "ERA LOCK: Atemporal, era-agnostic underground workshop — no overt historical markers (NOT medieval, NOT steampunk, NOT cyberpunk, NOT futuristic sci‑fi).",
          "FORBIDDEN: Medieval castle architecture, Viking/Norse runes, Celtic knotwork, Samurai armor, kabuto, katana, Torii gates, Gothic arches or stained glass, Art Deco motifs, Roman columns or Greek statues, Renaissance paintings, Fantasy dwarven halls (Moria style), Elven motifs, Steampunk gears and brass goggles, Cyberpunk neon and holograms, Futuristic sci‑fi technology, Electric lighting (bulbs, LEDs, fluorescents), Colored stage lighting, Windows, skylights, daylight shafts, Modern power tools (angle grinder, plasma cutter, electric welder), CNC machines, Computer screens or digital displays, Visible wiring and extension cords, Chrome or stainless steel polished finishes, Plastic components, Concrete or tiled walls/floors, White painted walls, Brand logos or modern signage, Safety signage and OSHA tape, Religious iconography, National flags or symbols, Text inscriptions in any language, Ornate jewelry inlays, gemstones, gold leaf, Stylized cultural masks (Kabuki, Oni, Venetian, tribal), Weapons beyond smithing tools, Firearms, Magical effects (glowing runes, enchanted light), Smoke machines or theatrical fog, Crowds or additional people; the blacksmith is alone, External light sources other than the forge fire, Countdown timers or digital clocks",
          "COLOR_PALETTE: Firelit amber/orange highlights with deep charcoal and black shadows; gritty, high contrast.",
          "ARCHITECTURE: Natural rough cave walls and stone; minimal, utilitarian forge fixtures only.",
          "LIGHTING: Single practical source: forge/fire glow; chiaroscuro; no fill, rim, overhead, or electric lights.",
          "MATERIALS: Black iron/steel, raw stone, soot, ash; avoid polished or decorative finishes.",
          "PROPS: Manual smithing tools only (anvil, hammer, tongs); no powered equipment.",
          "COSTUME: Functional, neutral workwear (heavy apron, gloves); no cultural insignia or ornament.",
          "SET_DRESSING: Sparse, utilitarian; focus on labor and tools; no signage, logos, or decorative motifs.",
          "MOOD: Tense, gritty, urgent; physical exertion emphasized by sparks and darkness.",
          "Shot-specific: Show the moment of hammer contact with the red-hot mask and a violent eruption of bright orange sparks; his face should be briefly illuminated by the sparks.",
          "Shot-specific: No magical glow effects or colored lighting beyond the forge fire and natural sparks.",
          "Shot-specific: The blacksmith remains alone in frame."
        ]
      }
    }
  ]
}
```
