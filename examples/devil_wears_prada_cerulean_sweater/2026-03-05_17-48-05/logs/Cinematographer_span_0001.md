# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 30c95b42e8c84355
- **Session ID**: dataset_devil_wears_prada_cerulean_sweater_2026-03-05_17-48-05
- **Timestamp**: 2026-03-05 17:49:40
- **Duration**: 40.39s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3601
- **completion_tokens**: 3472
- **total_tokens**: 7073

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
- **LOCATION LOCK**: Manhattan, New York, USA
- **ERA LOCK**: Mid-2000s American fashion industry
- **FORBIDDEN ELEMENTS**: warm rustic decor, Mediterranean architecture, bohemian clutter, runway show environment, boutique retail space
- **STYLE OVERRIDES**:
  * color_palette: cool, desaturated editorial tones with cerulean accent
  * architecture: modern corporate office with glass, chrome, minimalist lines
  * wardrobe: high-end fashion editorial attire

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Manhattan, New York, USA
  - ERA LOCK: Mid-2000s American fashion industry
  - FORBIDDEN: warm rustic decor, Mediterranean architecture, bohemian clutter, runway show environment, boutique retail space
  - COLOR_PALETTE: cool, desaturated editorial tones with cerulean accent
  - ARCHITECTURE: modern corporate office with glass, chrome, minimalist lines
  - WARDROBE: high-end fashion editorial attire
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Mid-2000s, Manhattan fashion editorial office
Global Mood: Tense, freezing contempt; meticulous, intimidating scrutiny
Key Events: Silent visual standoff between Miranda and Andy, Miranda’s gaze dismantles Andy’s confidence, Miranda’s dismissive voiceover defines the sweater as cerulean
Cultural Context: High-fashion editorial hierarchy where precise color language signals expertise and power; junior assistants navigate exacting standards and silent authority.

### GLOBAL VISUAL STYLE
Cold, minimalist high-fashion editorial aesthetic; sterile lighting; tight, highly detailed close-ups; emphasis on micro-expressions and texture; subdued palette with a cerulean accent.

### CHARACTER ASSETS
- ID: char_miranda_priestly
  Name: Miranda Priestly
  Visual: Imposing fashion editor with sleek silver bob, gold-rimmed glasses, razor-sharp gaze; immaculate high-end presence in a cold-toned office.
  Clothing: Tailored couture suits, monochrome palettes, discreet luxury accessories (gold-rimmed glasses), heels.
  Personality: Cold, calculating, perfectionist; exacting authority; intimidating poise.
  Backstory: Powerful fashion editor known for uncompromising standards; com
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_miranda_cold_stare",
      "staging_layer": {
        "duration_seconds": 3.6,
        "camera": {
          "shot_scale": "CU",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "sterile cool high-key office with subtle rim from glass reflections",
        "environment_id": "loc_int_fashion_office",
        "entities": [
          {
            "asset_id": "char_miranda_priestly",
            "position": "frame_right",
            "action_state": "looking_offscreen_left"
          },
          {
            "asset_id": "prop_gold_rimmed_glasses",
            "position": "frame_right",
            "action_state": "worn_on_face_glinting"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York, USA",
          "ERA LOCK: Mid-2000s American fashion industry",
          "FORBIDDEN: warm rustic decor, Mediterranean architecture, bohemian clutter, runway show environment, boutique retail space",
          "COLOR_PALETTE: cool, desaturated editorial tones with cerulean accent",
          "ARCHITECTURE: modern corporate office with glass, chrome, minimalist lines",
          "WARDROBE: high-end fashion editorial attire",
          "Miranda framed frame_right, gaze oriented offscreen_left toward Andy",
          "Glasses must catch a cool specular highlight; avoid any warm cast"
        ]
      }
    },
    {
      "shot_id": "shot_02_sweater_closeup_cerulean",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "ECU",
          "angle": "eye_level",
          "movement": "slow_dolly_in with rack_focus"
        },
        "lighting": "sterile cool high-key with soft side light to reveal knit texture",
        "environment_id": "loc_int_fashion_office",
        "entities": [
          {
            "asset_id": "char_andrea_sachs",
            "position": "center_fg",
            "action_state": "standing_still"
          },
          {
            "asset_id": "prop_cerulean_sweater",
            "position": "center_fg",
            "action_state": "worn_on_torso_texture_emphasized"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Manhattan, New York, USA",
          "ERA LOCK: Mid-2000s American fashion industry",
          "FORBIDDEN: warm rustic decor, Mediterranean architecture, bohemian clutter, runway show environment, boutique retail space",
          "COLOR_PALETTE: cool, desaturated editorial tones with cerulean accent",
          "ARCHITECTURE: modern corporate office with glass, chrome, minimalist lines",
          "WARDROBE: high-end fashion editorial attire",
          "Cerulean sweater must be the most saturated element; surrounding tones remain cool and desaturated",
          "Texture/pilling of knit must be readable; minimize specular glare via soft side light and slight rack_focus",
          "Background should fall off to soft bokeh; any visible environment must read as glass/chrome office surfaces"
        ]
      }
    }
  ]
}
```
