# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 542f92ea31d54213
- **Session ID**: dataset_pulp_fiction_royale_with_cheese_2026-03-05_17-47-59
- **Timestamp**: 2026-03-05 17:49:52
- **Duration**: 30.77s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3691
- **completion_tokens**: 4351
- **total_tokens**: 8042

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
- **LOCATION LOCK**: Los Angeles, California, USA (NOT New York, NOT Europe)
- **ERA LOCK**: 1990s America
- **FORBIDDEN ELEMENTS**: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside
- **STYLE OVERRIDES**:
  * color_palette: Warm California morning sunlight, strong contrast
  * architecture: Automotive interior only, no exterior landmarks
  * wardrobe: Crisp black suits, white shirts, narrow ties

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Los Angeles, California, USA (NOT New York, NOT Europe)
  - ERA LOCK: 1990s America
  - FORBIDDEN: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside
  - COLOR_PALETTE: Warm California morning sunlight, strong contrast
  - ARCHITECTURE: Automotive interior only, no exterior landmarks
  - WARDROBE: Crisp black suits, white shirts, narrow ties
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: 1990s Los Angeles morning
Global Mood: Relaxed, cool, rhythmic
Key Events: Vincent Vega and Jules Winnfield ride in a moving vintage car, smoking., Jules asks a question over the engine hum and shifting light., Vincent replies in voiceover: "They call it a Royale with Cheese."
Cultural Context: 1990s American urban culture; LA car-centric life; casual fast-food pop-culture banter.

### GLOBAL VISUAL STYLE
Naturalistic 1990s neo-noir; bright Californian sunlight; tight locked close-ups; minimal palette (black suits, tan leather); rhythmic, casual pacing; emphasis on pop-culture dialogue.

### CHARACTER ASSETS
- ID: char_vincent_vega
  Name: Vincent Vega
  Visual: A man in a crisp black suit, relaxed and composed, smoking casually in a cramped leather car interior; his face catches shifting bright Los Angeles sunlight and moving street shadows.
  Clothing: Crisp black suit, white shirt, narrow tie; minimal accessories.
  Personality: Cool, detached, amiable; goes with the flow, observant, unhurried.
  Backstory: Professional partner to Jules; accustomed to casual banter during drives.
  Motivation: Share a pop-culture observation and keep the ride relaxed.
-
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_sunlit_ride_smoke",
      "staging_layer": {
        "duration_seconds": 3.8,
        "camera": {
          "shot_scale": "MS",
          "angle": "eye_level",
          "movement": "static"
        },
        "lighting": "warm California morning sunlight, strong contrast, shifting window patterns",
        "environment_id": "loc_int_moving_car",
        "entities": [
          {
            "asset_id": "char_jules_winnfield",
            "position": "frame_left_seated",
            "action_state": "smoking_casual_looking_ahead"
          },
          {
            "asset_id": "char_vincent_vega",
            "position": "frame_right_seated",
            "action_state": "smoking_casual_looking_ahead"
          },
          {
            "asset_id": "prop_cigarette",
            "position": "frame_left_hand",
            "action_state": "tapping_ash"
          },
          {
            "asset_id": "prop_cigarette",
            "position": "frame_right_hand",
            "action_state": "glowing_ember_exhale"
          },
          {
            "asset_id": "prop_vintage_car",
            "position": "background_full",
            "action_state": "moving_interior_vibration"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Los Angeles, California, USA (NOT New York, NOT Europe)",
          "ERA LOCK: 1990s America",
          "FORBIDDEN: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside",
          "COLOR_PALETTE: Warm California morning sunlight, strong contrast",
          "ARCHITECTURE: Automotive interior only, no exterior landmarks",
          "WARDROBE: Crisp black suits, white shirts, narrow ties",
          "Two-shot — both characters must be visible within the frame",
          "Camera locked to car interior — no exterior landmarks visible through windows",
          "Shifting sunlight and passing shadows must be evident across faces",
          "Windows show abstract motion only (blurred), no recognizable LA landmarks",
          "Cigarette smoke trails should be visible in the air"
        ]
      }
    },
    {
      "shot_id": "shot_02_jules_asks_question",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "OTS",
          "angle": "eye_level",
          "movement": "static"
        },
        "lighting": "warm California morning sunlight, strong contrast, shifting window patterns",
        "environment_id": "loc_int_moving_car",
        "entities": [
          {
            "asset_id": "char_jules_winnfield",
            "position": "center_fg",
            "action_state": "turning_to_vincent_speaking"
          },
          {
            "asset_id": "char_vincent_vega",
            "position": "foreground_right_shoulder",
            "action_state": "listening_offscreen_left"
          },
          {
            "asset_id": "prop_cigarette",
            "position": "center_fg_hand",
            "action_state": "held_between_fingers"
          },
          {
            "asset_id": "prop_vintage_car",
            "position": "background",
            "action_state": "moving_interior_vibration"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Los Angeles, California, USA (NOT New York, NOT Europe)",
          "ERA LOCK: 1990s America",
          "FORBIDDEN: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside",
          "COLOR_PALETTE: Warm California morning sunlight, strong contrast",
          "ARCHITECTURE: Automotive interior only, no exterior landmarks",
          "WARDROBE: Crisp black suits, white shirts, narrow ties",
          "Maintain OTS composition with Vincent's shoulder in the right foreground framing Jules",
          "Eye-level perspective must be maintained",
          "Camera locked to car interior — no exterior landmarks visible through windows",
          "Windows show abstract motion only (blurred), no recognizable LA landmarks",
          "Cigarette smoke visible around Jules as he speaks"
        ]
      }
    },
    {
      "shot_id": "shot_03_vincent_voiceover_reply",
      "staging_layer": {
        "duration_seconds": 2.5,
        "camera": {
          "shot_scale": "CU",
          "angle": "eye_level",
          "movement": "rack_focus"
        },
        "lighting": "warm California morning sunlight, strong contrast, shifting window patterns",
        "environment_id": "loc_int_moving_car",
        "entities": [
          {
            "asset_id": "char_vincent_vega",
            "position": "center_fg",
            "action_state": "subtle_smirk_looking_ahead"
          },
          {
            "asset_id": "prop_cigarette",
            "position": "frame_right_hand",
            "action_state": "smoldering_smoke_trail"
          },
          {
            "asset_id": "prop_vintage_car",
            "position": "background",
            "action_state": "chrome_reflections_soft"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Los Angeles, California, USA (NOT New York, NOT Europe)",
          "ERA LOCK: 1990s America",
          "FORBIDDEN: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside",
          "COLOR_PALETTE: Warm California morning sunlight, strong contrast",
          "ARCHITECTURE: Automotive interior only, no exterior landmarks",
          "WARDROBE: Crisp black suits, white shirts, narrow ties",
          "Hold tight CU on Vincent; Jules should not be visible in this frame",
          "Use rack focus to settle on Vincent's eyes (from cigarette ember or dashboard details)",
          "Shifting sunlight and passing shadows must remain on Vincent's face",
          "Camera locked to car interior — no exterior landmarks visible through windows",
          "Windows show abstract motion only (blurred), no recognizable LA landmarks"
        ]
      }
    }
  ]
}
```
