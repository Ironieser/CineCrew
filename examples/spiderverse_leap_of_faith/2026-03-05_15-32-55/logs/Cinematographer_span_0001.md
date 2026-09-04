# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 2cc9b254b5c04b25
- **Session ID**: dataset_spiderverse_leap_of_faith_2026-03-05_15-32-55
- **Timestamp**: 2026-03-05 15:36:14
- **Duration**: 71.64s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3795
- **completion_tokens**: 4824
- **total_tokens**: 8619

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
- **LOCATION LOCK**: New York City, USA (NOT Los Angeles, NOT Tokyo)
- **ERA LOCK**: Contemporary urban setting
- **FORBIDDEN ELEMENTS**: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes
- **STYLE OVERRIDES**:
  * color_palette: Neon blues, magentas, cyans; high-contrast blacks
  * architecture: Modern glass-and-steel skyscrapers; urban rooftops
  * cinematography: Comic-book framing, halftone textures, extreme angles, 180-degree inversion
  * frame_rate: Variable frame rates to emphasize emotion and motion

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: New York City, USA (NOT Los Angeles, NOT Tokyo)
  - ERA LOCK: Contemporary urban setting
  - FORBIDDEN: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes
  - COLOR_PALETTE: Neon blues, magentas, cyans; high-contrast blacks
  - ARCHITECTURE: Modern glass-and-steel skyscrapers; urban rooftops
  - CINEMATOGRAPHY: Comic-book framing, halftone textures, extreme angles, 180-degree inversion
  - FRAME_RATE: Variable frame rates to emphasize emotion and motion
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Contemporary New York City, night
Global Mood: Exhilarating, vertigo-inducing, courageous, introspective
Key Events: A young superhero stands at the extreme edge of a New York skyscraper., He falls backward into the neon-lit abyss of the city., The camera violently inverts 180°, creating the illusion of rising into the sky., He spreads his arms, embracing a leap of faith as shattering glass sounds echo.
Cultural Context: Superhero genre; urban New York skyline; stylized comic-book/animation language using halftones, bold neon, and variable frame rates.

### GLOBAL VISUAL STYLE
Highly stylized, neon-lit comic book aesthetic with halftone textures, bold contrasts, kinetic motion blur, and shifting frame rates; dynamic camera, including 180-degree inversion to dramatize the leap of faith.

### CHARACTER ASSETS
- ID: char_young_superhero
  Name: Young Superhero
  Visual: Young masked hero at skyscraper edge; athletic build; wears black suit under a green jac
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_edge_breath_poise",
      "staging_layer": {
        "duration_seconds": 3.2,
        "camera": {
          "shot_scale": "MS",
          "angle": "dutch",
          "movement": "slow_dolly_in"
        },
        "lighting": "neon-lit night high-contrast rimlight; overcast soft fill from city glow",
        "environment_id": "loc_ext_new_york_skyscraper_rooftop",
        "entities": [
          {
            "asset_id": "char_young_superhero",
            "position": "frame_right",
            "action_state": "toes_over_ledge, steadying breath, gaze outward"
          },
          {
            "asset_id": "prop_green_jacket",
            "position": "frame_right",
            "action_state": "fluttering_in_wind, rimlit edge"
          },
          {
            "asset_id": "prop_red_blue_sneakers",
            "position": "frame_right",
            "action_state": "on_ledge_edge, toes_over"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: New York City, USA (NOT Los Angeles, NOT Tokyo)",
          "ERA LOCK: Contemporary urban setting",
          "FORBIDDEN: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes",
          "COLOR_PALETTE: Neon blues, magentas, cyans; high-contrast blacks",
          "ARCHITECTURE: Modern glass-and-steel skyscrapers; urban rooftops",
          "CINEMATOGRAPHY: Comic-book framing, halftone textures, extreme angles, 180-degree inversion",
          "FRAME_RATE: Variable frame rates to emphasize emotion and motion",
          "Wardrobe continuity: green jacket and red-and-blue sneakers must be visible as accents.",
          "Screen direction: rooftop ledge anchors frame_right; city depth expands to frame_left.",
          "Maintain low-key silhouette with neon rim on shoulders and jawline."
        ]
      }
    },
    {
      "shot_id": "shot_02_backward_fall_abyss",
      "staging_layer": {
        "duration_seconds": 2.6,
        "camera": {
          "shot_scale": "LS",
          "angle": "high",
          "movement": "crane_over_ledge_then_drop_follow"
        },
        "lighting": "neon-lit night with deep city glow; low-key high-contrast edges",
        "environment_id": "loc_ext_new_york_skyscraper_rooftop",
        "entities": [
          {
            "asset_id": "char_young_superhero",
            "position": "center_fg",
            "action_state": "falling_backward_from_ledge, arms_tucked"
          },
          {
            "asset_id": "prop_green_jacket",
            "position": "center_fg",
            "action_state": "whip_in_wind_during_drop"
          },
          {
            "asset_id": "prop_red_blue_sneakers",
            "position": "center_fg",
            "action_state": "leaving_ledge, soles_flash_in_neon"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: New York City, USA (NOT Los Angeles, NOT Tokyo)",
          "ERA LOCK: Contemporary urban setting",
          "FORBIDDEN: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes",
          "COLOR_PALETTE: Neon blues, magentas, cyans; high-contrast blacks",
          "ARCHITECTURE: Modern glass-and-steel skyscrapers; urban rooftops",
          "CINEMATOGRAPHY: Comic-book framing, halftone textures, extreme angles, 180-degree inversion",
          "FRAME_RATE: Variable frame rates to emphasize emotion and motion",
          "Maintain screen direction from shot_01: he releases from frame_right ledge and falls toward frame_bottom-left.",
          "Wind interaction: jacket flutters aggressively; motion blur streaks align with fall vector.",
          "Keep rooftop glass-and-steel materials in frame briefly as camera tips over the edge."
        ]
      }
    },
    {
      "shot_id": "shot_03_world_inverts_rising",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "MCU",
          "angle": "dutch",
          "movement": "rapid_180_roll_with_speed_ramp"
        },
        "lighting": "silhouette backlight neon glow with halftone streaks; high-contrast",
        "environment_id": "loc_ext_new_york_skyscraper_rooftop",
        "entities": [
          {
            "asset_id": "char_young_superhero",
            "position": "center_fg",
            "action_state": "continuing_freefall, orientation_flips_to_appear_rising"
          },
          {
            "asset_id": "prop_green_jacket",
            "position": "center_fg",
            "action_state": "trailing_streamers_in_roll, rimlit edges"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: New York City, USA (NOT Los Angeles, NOT Tokyo)",
          "ERA LOCK: Contemporary urban setting",
          "FORBIDDEN: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes",
          "COLOR_PALETTE: Neon blues, magentas, cyans; high-contrast blacks",
          "ARCHITECTURE: Modern glass-and-steel skyscrapers; urban rooftops",
          "CINEMATOGRAPHY: Comic-book framing, halftone textures, extreme angles, 180-degree inversion",
          "FRAME_RATE: Variable frame rates to emphasize emotion and motion",
          "Execute a full 180-degree inversion roll within this shot; horizon flips once, creating rising illusion.",
          "Use kinetic motion blur and neon streaks during the roll; maintain hero's face silhouette readable.",
          "Maintain continuity: wardrobe (green jacket, red-and-blue sneakers) and neon rimlight persist through roll."
        ]
      }
    },
    {
      "shot_id": "shot_04_arms_wide_leap",
      "staging_layer": {
        "duration_seconds": 3.6,
        "camera": {
          "shot_scale": "LS",
          "angle": "undershot",
          "movement": "tracking_fall_stabilized_slow_dolly_in"
        },
        "lighting": "neon backlight with specular glass highlights; high-contrast silhouette",
        "environment_id": "loc_ext_new_york_skyscraper_rooftop",
        "entities": [
          {
            "asset_id": "char_young_superhero",
            "position": "center_fg",
            "action_state": "arms_spread_wide_in_freefall, embracing_leap"
          },
          {
            "asset_id": "prop_green_jacket",
            "position": "center_fg",
            "action_state": "billowing_wingspread_silhouette"
          },
          {
            "asset_id": "prop_red_blue_sneakers",
            "position": "center_fg",
            "action_state": "toes_pointed_down, trailing_motion_lines"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: New York City, USA (NOT Los Angeles, NOT Tokyo)",
          "ERA LOCK: Contemporary urban setting",
          "FORBIDDEN: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes",
          "COLOR_PALETTE: Neon blues, magentas, cyans; high-contrast blacks",
          "ARCHITECTURE: Modern glass-and-steel skyscrapers; urban rooftops",
          "CINEMATOGRAPHY: Comic-book framing, halftone textures, extreme angles, 180-degree inversion",
          "FRAME_RATE: Variable frame rates to emphasize emotion and motion",
          "Maintain post-inversion orientation from shot_03 so hero appears to ascend; arms fully extended within frame.",
          "Silhouette readability: strong rimlight on shoulders, forearms, and jacket hem; specular hints imply shattering glass off-screen.",
          "Keep background city parallax moving upward relative to frame to sustain rising illusion."
        ]
      }
    }
  ]
}
```
