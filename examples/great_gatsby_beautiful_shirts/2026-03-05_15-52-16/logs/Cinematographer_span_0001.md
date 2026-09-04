# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 45d29e4d81744584
- **Session ID**: dataset_great_gatsby_beautiful_shirts_2026-03-05_15-52-16
- **Timestamp**: 2026-03-05 15:54:27
- **Duration**: 29.31s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3806
- **completion_tokens**: 3786
- **total_tokens**: 7592

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
- **LOCATION LOCK**: North Shore, Long Island, New York, USA
- **ERA LOCK**: Early 1920s Jazz Age America
- **FORBIDDEN ELEMENTS**: modern technology, smartphones, contemporary casualwear, minimalist interiors, mid-century or later design cues
- **STYLE OVERRIDES**:
  * color_palette: soft pastels with warm sunlight
  * lighting: diffused natural daylight, glowing highlights
  * set_decoration: sumptuous, high-end 1920s luxury

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: North Shore, Long Island, New York, USA
  - ERA LOCK: Early 1920s Jazz Age America
  - FORBIDDEN: modern technology, smartphones, contemporary casualwear, minimalist interiors, mid-century or later design cues
  - COLOR_PALETTE: soft pastels with warm sunlight
  - LIGHTING: diffused natural daylight, glowing highlights
  - SET_DECORATION: sumptuous, high-end 1920s luxury
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Early 1920s, Jazz Age
Global Mood: Lavish, romantic, nostalgic; awe melting into aching melancholy.
Key Events: Gatsby jubilantly tosses pastel silk and linen shirts from an upper wardrobe balcony., Shirts drift in extreme slow-motion, billowing and settling on a massive plush bed., Daisy laughs, then, overwhelmed, buries her face in the shirts and weeps., A soft voiceover: "They're such beautiful shirts... I've never seen such beautiful shirts before."
Cultural Context: American Jazz Age excess and conspicuous consumption; wealth as romantic spectacle; emotional fragility beneath opulence.

### GLOBAL VISUAL STYLE
Opulent Jazz Age glamour; sunlit pastels; diffused natural light; extreme slow-motion elegance; romantic yet bittersweet tone.

### CHARACTER ASSETS
- ID: char_gatsby
  Name: Gatsby
  Visual: Well-groomed man in his thirties, handsome, athletic, exuding effortless wealth and polish; bright eyes, confident smile.
  Clothing: Impeccable 1920s tailoring; pastel silk and linen shirts; crisp trousers; polished oxfords.
  Personality: Romantic, performative, idealistic, restless, desperate to impress.
  Backstory: Extremely wealthy host who curates opulence; past feelings for Daisy fuel grand gestures.
  Motivatio
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_gatsby_tosses_shirts",
      "staging_layer": {
        "duration_seconds": 4.5,
        "camera": {
          "shot_scale": "LS",
          "angle": "low",
          "movement": "slow_tilt_up_follow_shirts"
        },
        "lighting": "diffused natural daylight, glowing highlights",
        "environment_id": "loc_int_gatsbys_bedroom",
        "entities": [
          {
            "asset_id": "char_gatsby",
            "position": "background_upper_center",
            "action_state": "tossing_shirts_down"
          },
          {
            "asset_id": "prop_open_wardrobe",
            "position": "background_center",
            "action_state": "balcony_visible"
          },
          {
            "asset_id": "prop_pastel_shirts",
            "position": "midair_center",
            "action_state": "cascading_downward"
          },
          {
            "asset_id": "prop_plush_bed",
            "position": "foreground_lower_right",
            "action_state": "awaiting_shirts"
          },
          {
            "asset_id": "prop_massive_windows",
            "position": "background_left",
            "action_state": "gauzy_curtains_swaying"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: North Shore, Long Island, New York, USA",
          "ERA LOCK: Early 1920s Jazz Age America",
          "FORBIDDEN: modern technology, smartphones, contemporary casualwear, minimalist interiors, mid-century or later design cues",
          "COLOR_PALETTE: soft pastels with warm sunlight",
          "LIGHTING: diffused natural daylight, glowing highlights",
          "SET_DECORATION: sumptuous, high-end 1920s luxury",
          "Gatsby must be framed from a low angle to emphasize spectacle and status",
          "Open wardrobe balcony must remain visible in frame",
          "Shirts motion must be captured in extreme slow-motion as they leave Gatsby’s hands",
          "Maintain pastel fabric tones; avoid saturated primaries"
        ]
      }
    },
    {
      "shot_id": "shot_02_shirts_fall_settle",
      "staging_layer": {
        "duration_seconds": 6.0,
        "camera": {
          "shot_scale": "MCU",
          "angle": "overhead",
          "movement": "slow_crane_down_follow_fabric"
        },
        "lighting": "diffused natural daylight, glowing highlights",
        "environment_id": "loc_int_gatsbys_bedroom",
        "entities": [
          {
            "asset_id": "prop_pastel_shirts",
            "position": "center_fg",
            "action_state": "billowing_glide"
          },
          {
            "asset_id": "prop_plush_bed",
            "position": "center_bg",
            "action_state": "receiving_shirts_gently"
          },
          {
            "asset_id": "prop_massive_windows",
            "position": "background_upper",
            "action_state": "soft_glow_through_gauze"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: North Shore, Long Island, New York, USA",
          "ERA LOCK: Early 1920s Jazz Age America",
          "FORBIDDEN: modern technology, smartphones, contemporary casualwear, minimalist interiors, mid-century or later design cues",
          "COLOR_PALETTE: soft pastels with warm sunlight",
          "LIGHTING: diffused natural daylight, glowing highlights",
          "SET_DECORATION: sumptuous, high-end 1920s luxury",
          "Daisy’s line is voiceover only; Daisy and Gatsby are NOT visible in this shot",
          "Fabric movement must be rendered in extreme slow-motion",
          "Use shallow depth of field to emphasize silk and linen textures",
          "No harsh shadows; maintain gentle overhead perspective onto bed"
        ]
      }
    },
    {
      "shot_id": "shot_03_daisy_weeps_shirts",
      "staging_layer": {
        "duration_seconds": 5.5,
        "camera": {
          "shot_scale": "CU",
          "angle": "eye_level",
          "movement": "slow_dolly_in"
        },
        "lighting": "diffused natural daylight, glowing highlights",
        "environment_id": "loc_int_gatsbys_bedroom",
        "entities": [
          {
            "asset_id": "char_daisy",
            "position": "seated_center",
            "action_state": "laughing_then_burying_face_weeping"
          },
          {
            "asset_id": "prop_pastel_shirts",
            "position": "foreground_lower_center",
            "action_state": "piled_around_daisy"
          },
          {
            "asset_id": "prop_plush_bed",
            "position": "center_bg",
            "action_state": "supporting_daisy"
          },
          {
            "asset_id": "prop_massive_windows",
            "position": "background_soft",
            "action_state": "warm_backlight_glow"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: North Shore, Long Island, New York, USA",
          "ERA LOCK: Early 1920s Jazz Age America",
          "FORBIDDEN: modern technology, smartphones, contemporary casualwear, minimalist interiors, mid-century or later design cues",
          "COLOR_PALETTE: soft pastels with warm sunlight",
          "LIGHTING: diffused natural daylight, glowing highlights",
          "SET_DECORATION: sumptuous, high-end 1920s luxury",
          "Maintain eye-level intimacy on Daisy throughout the shot",
          "Keep Daisy’s tears subtle and luminous; avoid harsh streaking",
          "Pastel shirt palette must remain consistent with previous shots",
          "Background windows should stay softly blown with gauzy curtains; no hard speculars"
        ]
      }
    }
  ]
}
```
