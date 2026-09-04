# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 2369461831324e3f
- **Session ID**: dataset_devil_wears_prada_temporal_tracking_2026-03-05_15-57-12
- **Timestamp**: 2026-03-05 16:00:06
- **Duration**: 69.75s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4060
- **completion_tokens**: 5559
- **total_tokens**: 9619

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
- **LOCATION LOCK**: Manhattan, New York City, USA
- **ERA LOCK**: Contemporary (unspecified exact year)
- **STYLE OVERRIDES**:
  * color_palette: sleek monochrome with dark green, white, black accents
  * architecture: dense New York urban streetscape, contemporary signage, yellow cabs

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Manhattan, New York City, USA
  - ERA LOCK: Contemporary (unspecified exact year)
  - COLOR_PALETTE: sleek monochrome with dark green, white, black accents
  - ARCHITECTURE: dense New York urban streetscape, contemporary signage, yellow cabs
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Contemporary, Manhattan
Global Mood: Assertive, stylish, kinetic, transformational
Key Events: Andy power-walks along a bustling Manhattan street in a single smooth tracking shot., Passing behind a yellow taxi triggers a seamless outfit change to a white tweed look with thigh-high Chanel boots., Passing behind a narrow streetlamp triggers a second seamless change to a sleek black evening jacket., The paper coffee cup remains perfectly aligned in her hand through all transitions; heel clicks and music drive momentum.
Cultural Context: Urban fashion-as-performance, Manhattan street-as-runway sensibility; brand-conscious styling and music-video pacing emphasize confidence and transformation.

### GLOBAL VISUAL STYLE
High-fashion, glossy urban aesthetic; smooth continuous tracking; seamless match-cut transformations; kinetic edit rhythm driven by heel clicks and pulsing music.

### CHARACTER ASSETS
- ID: char_andy
  Name: Andy
  Visual: Fashion-forward woman in her 20s–30s, confident posture, decisive stride, polished grooming; carries a paper coffee cup; aura of control; high heels clicking underscore her presence.
  Clothing: High-fashion outerwear transformations: heavy dark green double-breasted coat; white tweed coat with thigh-high Chanel boots; sleek tailored black evening jacket. Polished, runway-ready styling.
  Personality: Dominant, self-assured, stylish, relentless, focused; treats the city like her runway; unfazed by chaos; enjoys precise control and continuity.
  Backstory: A hi
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_confident_street_strut",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "MLS",
          "angle": "eye_level",
          "movement": "gimbal_parallel_track_left_to_right"
        },
        "lighting": "high-key daylight (overcast soft fill, glossy urban sheen)",
        "environment_id": "loc_ext_manhattan_street",
        "entities": [
          {
            "asset_id": "char_andy",
            "position": "center_fg",
            "action_state": "confident_power_walk, eyes_forward"
          },
          {
            "asset_id": "prop_paper_coffee_cup",
            "position": "center_fg",
            "action_state": "held_upright_aligned"
          },
          {
            "asset_id": "prop_dark_green_double_breasted_coat",
            "position": "center_fg",
            "action_state": "worn_in_motion, fabric_sway_with_stride"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York City, USA",
          "ERA LOCK: Contemporary (unspecified exact year)",
          "COLOR_PALETTE: sleek monochrome with dark green, white, black accents",
          "ARCHITECTURE: dense New York urban streetscape, contemporary signage, yellow cabs",
          "Maintain continuous left-to-right parallel tracking direction across the sequence",
          "Coffee cup must remain perfectly upright and occupy a consistent relative screen position near Andy’s torso"
        ]
      }
    },
    {
      "shot_id": "shot_02_taxi_occlusion_transform",
      "staging_layer": {
        "duration_seconds": 2.4,
        "camera": {
          "shot_scale": "LS",
          "angle": "eye_level",
          "movement": "gimbal_parallel_track_left_to_right"
        },
        "lighting": "high-key daylight (overcast soft fill, glossy urban sheen)",
        "environment_id": "loc_ext_manhattan_street",
        "entities": [
          {
            "asset_id": "char_andy",
            "position": "center_midground",
            "action_state": "stride_continues_behind_occluder_then_reemerge"
          },
          {
            "asset_id": "prop_paper_coffee_cup",
            "position": "center_midground",
            "action_state": "held_upright_aligned"
          },
          {
            "asset_id": "prop_dark_green_double_breasted_coat",
            "position": "center_midground",
            "action_state": "visible_pre-occlusion"
          },
          {
            "asset_id": "prop_white_tweed_coat",
            "position": "center_midground",
            "action_state": "visible_post-occlusion"
          },
          {
            "asset_id": "prop_thigh_high_chanel_boots",
            "position": "center_midground",
            "action_state": "visible_post-occlusion, rhythmic_stride"
          },
          {
            "asset_id": "prop_yellow_taxi",
            "position": "foreground_center",
            "action_state": "passes_left_to_right_as_full_occluder"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York City, USA",
          "ERA LOCK: Contemporary (unspecified exact year)",
          "COLOR_PALETTE: sleek monochrome with dark green, white, black accents",
          "ARCHITECTURE: dense New York urban streetscape, contemporary signage, yellow cabs",
          "Maintain continuous left-to-right parallel tracking direction across the sequence",
          "Transformation from dark green coat to white tweed + thigh-high Chanel boots must occur fully while taxi occludes Andy",
          "Taxi must pass between camera and Andy to achieve a single clean full-frame occlusion for the match cut",
          "Coffee cup must remain perfectly upright and in consistent relative screen position through occlusion"
        ]
      }
    },
    {
      "shot_id": "shot_03_white_look_stride",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "MS",
          "angle": "eye_level",
          "movement": "gimbal_parallel_track_left_to_right"
        },
        "lighting": "high-key daylight (overcast soft fill, glossy urban sheen)",
        "environment_id": "loc_ext_manhattan_street",
        "entities": [
          {
            "asset_id": "char_andy",
            "position": "center_fg",
            "action_state": "assertive_strut, eyes_forward"
          },
          {
            "asset_id": "prop_paper_coffee_cup",
            "position": "center_fg",
            "action_state": "held_upright_aligned"
          },
          {
            "asset_id": "prop_white_tweed_coat",
            "position": "center_fg",
            "action_state": "worn_in_motion, crisp_texture_catches_light"
          },
          {
            "asset_id": "prop_thigh_high_chanel_boots",
            "position": "lower_frame_center",
            "action_state": "heel_clicks_in_step"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York City, USA",
          "ERA LOCK: Contemporary (unspecified exact year)",
          "COLOR_PALETTE: sleek monochrome with dark green, white, black accents",
          "ARCHITECTURE: dense New York urban streetscape, contemporary signage, yellow cabs",
          "Maintain continuous left-to-right parallel tracking direction across the sequence",
          "Match Andy’s position and stride continuity from Shot 02; no jump in speed or screen position",
          "Coffee cup must remain perfectly upright and in consistent relative screen position"
        ]
      }
    },
    {
      "shot_id": "shot_04_streetlamp_second_transform",
      "staging_layer": {
        "duration_seconds": 2.2,
        "camera": {
          "shot_scale": "MCU",
          "angle": "eye_level",
          "movement": "gimbal_parallel_track_left_to_right"
        },
        "lighting": "high-key daylight (overcast soft fill, glossy urban sheen)",
        "environment_id": "loc_ext_manhattan_street",
        "entities": [
          {
            "asset_id": "char_andy",
            "position": "center_fg",
            "action_state": "passes_behind_streetlamp_then_reappears"
          },
          {
            "asset_id": "prop_paper_coffee_cup",
            "position": "center_fg",
            "action_state": "held_upright_aligned"
          },
          {
            "asset_id": "prop_white_tweed_coat",
            "position": "center_fg",
            "action_state": "visible_pre-occlusion_upper_body"
          },
          {
            "asset_id": "prop_black_evening_jacket",
            "position": "center_fg",
            "action_state": "visible_post-occlusion_upper_body"
          },
          {
            "asset_id": "prop_narrow_streetlamp",
            "position": "foreground_center",
            "action_state": "brief_vertical_occlusion_sweeps_across_frame"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York City, USA",
          "ERA LOCK: Contemporary (unspecified exact year)",
          "COLOR_PALETTE: sleek monochrome with dark green, white, black accents",
          "ARCHITECTURE: dense New York urban streetscape, contemporary signage, yellow cabs",
          "Maintain continuous left-to-right parallel tracking direction across the sequence",
          "Transformation from white tweed to black evening jacket must be timed to the streetlamp’s occlusion on Andy’s upper body",
          "Streetlamp should bisect the frame vertically as the occluder; no other objects should block the view",
          "Coffee cup must remain perfectly upright and in consistent relative screen position"
        ]
      }
    },
    {
      "shot_id": "shot_05_black_jacket_finish",
      "staging_layer": {
        "duration_seconds": 3.6,
        "camera": {
          "shot_scale": "MLS",
          "angle": "low",
          "movement": "gimbal_parallel_track_left_to_right_slight_push_in"
        },
        "lighting": "high-key daylight (overcast soft fill, glossy urban sheen)",
        "environment_id": "loc_ext_manhattan_street",
        "entities": [
          {
            "asset_id": "char_andy",
            "position": "center_fg",
            "action_state": "dominant_runway_stride, chin_up"
          },
          {
            "asset_id": "prop_paper_coffee_cup",
            "position": "center_fg",
            "action_state": "held_upright_aligned"
          },
          {
            "asset_id": "prop_black_evening_jacket",
            "position": "center_fg",
            "action_state": "worn_in_motion, sharp_lapels_catch_light"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York City, USA",
          "ERA LOCK: Contemporary (unspecified exact year)",
          "COLOR_PALETTE: sleek monochrome with dark green, white, black accents",
          "ARCHITECTURE: dense New York urban streetscape, contemporary signage, yellow cabs",
          "Maintain continuous left-to-right parallel tracking direction across the sequence",
          "Subtle push-in must not disrupt lateral continuity or Andy’s central screen position",
          "Low angle should reinforce power without revealing non-contemporary elements",
          "Coffee cup must remain perfectly upright and in consistent relative screen position"
        ]
      }
    }
  ]
}
```
