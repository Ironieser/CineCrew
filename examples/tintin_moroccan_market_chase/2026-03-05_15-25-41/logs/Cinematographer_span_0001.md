# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 2bdd77fb27b84af1
- **Session ID**: dataset_tintin_moroccan_market_chase_2026-03-05_15-25-41
- **Timestamp**: 2026-03-05 15:28:33
- **Duration**: 90.47s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4267
- **completion_tokens**: 6489
- **total_tokens**: 10756

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
- **LOCATION LOCK**: Moroccan market district, North Africa (NOT European city)
- **ERA LOCK**: Daytime chase, contemporary with vintage tech
- **FORBIDDEN ELEMENTS**: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage
- **STYLE OVERRIDES**:
  * color_palette: warm ochres, terracotta, bright produce colors, sun-bleached neutrals
  * architecture: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks
  * lighting: harsh midday sun, hard shadows, dusty air bloom

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Moroccan market district, North Africa (NOT European city)
  - ERA LOCK: Daytime chase, contemporary with vintage tech
  - FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage
  - COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals
  - ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks
  - LIGHTING: harsh midday sun, hard shadows, dusty air bloom
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Midday; contemporary adventure with retro elements
Global Mood: Frenetic, high-stakes, catastrophic, kinetic
Key Events: High-speed tracking shot through a Moroccan market, Bearded companion aims a bazooka from the sidecar during the chase, Motorcycle smashes through fruit stands; oranges fly into the lens, Bike launches off a ramp of debris, Accidental bazooka discharge, Explosion strikes a distant dam, Floodwater surges into narrow streets, sweeping away the market
Cultural Context: North African medina-style marketplace: bustling vendors, colorful produce, sun-baked environment and tight alleyways.

### GLOBAL VISUAL STYLE
High-energy adventure with sun-baked North African palette, saturated colors, kinetic camera, practical stunts, comedic panic amid real danger, stylized realism.

### CHARACTER ASSETS
- ID: char_young_reporter
  Name: Young Reporter
  Visual: Young male reporter with a signature quiff, lithe build, agile rider; dust-streaked, focused eyes.
  Clothing: Light shirt, rolled sleeves, trousers, leather boots, goggle
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_reporter_blazes_market",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "MLS",
          "angle": "low",
          "movement": "tracking_vehicle_mount_low"
        },
        "lighting": "harsh midday sun, hard shadows, dusty air bloom",
        "environment_id": "loc_ext_moroccan_market",
        "entities": [
          {
            "asset_id": "prop_vintage_motorcycle_sidecar",
            "position": "center_fg",
            "action_state": "racing_forward"
          },
          {
            "asset_id": "char_young_reporter",
            "position": "frame_left",
            "action_state": "riding_focus_forward"
          },
          {
            "asset_id": "char_bearded_companion",
            "position": "frame_right",
            "action_state": "aiming_bazooka_wildly"
          },
          {
            "asset_id": "prop_bazooka",
            "position": "frame_right_fg",
            "action_state": "waving_unsteady"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Moroccan market district, North Africa (NOT European city)",
          "ERA LOCK: Daytime chase, contemporary with vintage tech",
          "FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage",
          "COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals",
          "ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks",
          "LIGHTING: harsh midday sun, hard shadows, dusty air bloom",
          "Keep camera slightly ahead-left of bike at bumper height; maintain low perspective to accentuate speed.",
          "Bazooka must remain visible frame-right in sidecar throughout this shot; dust trail behind wheels."
        ]
      }
    },
    {
      "shot_id": "shot_02_fruit_stands_explode",
      "staging_layer": {
        "duration_seconds": 2.5,
        "camera": {
          "shot_scale": "POV",
          "angle": "eye_level",
          "movement": "rapid_forward_POV"
        },
        "lighting": "harsh midday sun, hard shadows, dusty air bloom",
        "environment_id": "loc_ext_moroccan_market",
        "entities": [
          {
            "asset_id": "prop_fruit_stands",
            "position": "both_sides_fg",
            "action_state": "splintering_as_bike_blasts_through"
          },
          {
            "asset_id": "prop_oranges",
            "position": "center_fg",
            "action_state": "flying_toward_lens"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Moroccan market district, North Africa (NOT European city)",
          "ERA LOCK: Daytime chase, contemporary with vintage tech",
          "FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage",
          "COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals",
          "ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks",
          "LIGHTING: harsh midday sun, hard shadows, dusty air bloom",
          "POV is from the motorcycle heading forward through stalls; minimal bike visible (just a hint of handlebars acceptable).",
          "Oranges must impact toward camera; a quick splatter-on-lens gag is acceptable before cutting."
        ]
      }
    },
    {
      "shot_id": "shot_03_bike_launches_debris",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "LS",
          "angle": "low",
          "movement": "crane_up_follow"
        },
        "lighting": "harsh midday sun, hard shadows, dusty air bloom",
        "environment_id": "loc_ext_moroccan_market",
        "entities": [
          {
            "asset_id": "prop_debris_ramp",
            "position": "center_midground",
            "action_state": "improvised_from_toppled_crates_and_boards"
          },
          {
            "asset_id": "prop_vintage_motorcycle_sidecar",
            "position": "center_fg",
            "action_state": "launching_off_ramp"
          },
          {
            "asset_id": "char_young_reporter",
            "position": "frame_left",
            "action_state": "standing_on_pegs_launch"
          },
          {
            "asset_id": "char_bearded_companion",
            "position": "frame_right",
            "action_state": "bracing_with_bazooka"
          },
          {
            "asset_id": "prop_bazooka",
            "position": "frame_right_fg",
            "action_state": "clutched_pointing_forward"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Moroccan market district, North Africa (NOT European city)",
          "ERA LOCK: Daytime chase, contemporary with vintage tech",
          "FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage",
          "COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals",
          "ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks",
          "LIGHTING: harsh midday sun, hard shadows, dusty air bloom",
          "Ramp must read as organic market debris (wooden crates, boards, fabric) — no visible metal stunt ramp.",
          "Crane follows arc of bike to apex; retain low vantage to emphasize height and stakes."
        ]
      }
    },
    {
      "shot_id": "shot_04_bazooka_accidental_fire",
      "staging_layer": {
        "duration_seconds": 2.0,
        "camera": {
          "shot_scale": "CU",
          "angle": "dutch",
          "movement": "static_with_recoil_shake"
        },
        "lighting": "harsh midday sun, hard shadows, dusty air bloom",
        "environment_id": "loc_ext_moroccan_market",
        "entities": [
          {
            "asset_id": "char_bearded_companion",
            "position": "center_fg",
            "action_state": "recoiling_as_trigger_pulled_midair"
          },
          {
            "asset_id": "prop_bazooka",
            "position": "frame_left_fg",
            "action_state": "discharging_midair"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Moroccan market district, North Africa (NOT European city)",
          "ERA LOCK: Daytime chase, contemporary with vintage tech",
          "FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage",
          "COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals",
          "ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks",
          "LIGHTING: harsh midday sun, hard shadows, dusty air bloom",
          "Visible muzzle flash and backblast smoke; shoulder kick registers in frame.",
          "Background should be abstracted motion blur/sky and sun-bleached textiles — keep focus on face and bazooka mouth."
        ]
      }
    },
    {
      "shot_id": "shot_05_dam_explosion_boom",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "ELS",
          "angle": "eye_level",
          "movement": "slow_zoom_in"
        },
        "lighting": "blinding midday sun, hard contrast, heat haze",
        "environment_id": "loc_ext_distant_dam",
        "entities": [],
        "consistency_constraints": [
          "LOCATION LOCK: Moroccan market district, North Africa (NOT European city)",
          "ERA LOCK: Daytime chase, contemporary with vintage tech",
          "FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage",
          "COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals",
          "ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks",
          "LIGHTING: harsh midday sun, hard shadows, dusty air bloom",
          "Show monolithic concrete dam in arid hills; large explosion plume blooms off its face; no city skyline or modern glass buildings.",
          "Market stalls should NOT appear here; keep frame to dam, hills, and plume with heat haze shimmer."
        ]
      }
    },
    {
      "shot_id": "shot_06_flood_surge_pursues",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "LS",
          "angle": "low",
          "movement": "tracking_vehicle_mount_reverse"
        },
        "lighting": "harsh midday sun, hard shadows, dusty air bloom",
        "environment_id": "loc_ext_moroccan_market",
        "entities": [
          {
            "asset_id": "prop_vintage_motorcycle_sidecar",
            "position": "center_fg",
            "action_state": "speeding_away_from_flood"
          },
          {
            "asset_id": "char_young_reporter",
            "position": "frame_left",
            "action_state": "gunning_engine_glancing_back"
          },
          {
            "asset_id": "char_bearded_companion",
            "position": "frame_right",
            "action_state": "clutching_bazooka_eyes_wide"
          },
          {
            "asset_id": "prop_bazooka",
            "position": "frame_right_fg",
            "action_state": "held_tightly"
          },
          {
            "asset_id": "prop_fruit_stands",
            "position": "background_sides",
            "action_state": "being_swept_by_flood"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Moroccan market district, North Africa (NOT European city)",
          "ERA LOCK: Daytime chase, contemporary with vintage tech",
          "FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage",
          "COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals",
          "ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks",
          "LIGHTING: harsh midday sun, hard shadows, dusty air bloom",
          "Camera rig faces backward from a lead vehicle to keep the riders and towering flood wall in the same frame.",
          "Flood wall must visually tower at least a story above the riders; stalls and debris visibly swept along."
        ]
      }
    }
  ]
}
```
