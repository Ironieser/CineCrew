# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 6d523fb0ca7d4e1f
- **Session ID**: dataset_BetterCallSaul1_2026-03-05_09-06-38
- **Timestamp**: 2026-03-05 09:08:44
- **Duration**: 39.27s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4232
- **completion_tokens**: 6354
- **total_tokens**: 10586

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
- **FORBIDDEN ELEMENTS**: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements
- **STYLE OVERRIDES**:
  * color_palette: High-contrast black and white with isolated saturated color from TV
  * lighting: Harsh fluorescent in bakery; dim apartment lit by TV glow
  * season: Winter snowstorm

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements
  - COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV
  - LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow
  - SEASON: Winter snowstorm
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Unspecified winter; monochrome present with retro tech (VHS/VCR) and a past-era TV ad
Global Mood: Tense, melancholic, nostalgic isolation
Key Events: Gene mechanically kneads dough, eyes darting nervously in a mall bakery kitchen, He returns to a dark, rundown apartment amid a heavy snowstorm, He pushes an old VHS tape into a vintage VCR, The TV erupts in vivid color, piercing the monochrome room, Saul Goodman’s energetic ad plays; Gene silently watches the past he left behind
Cultural Context: Noir aesthetics; mall labor anonymity; VHS-era advertising tropes; contrast of monochrome present versus colorful media memory.

### GLOBAL VISUAL STYLE
Noir, high-contrast black and white with film grain; winter bleakness. Occasional saturated color bloom emanates only from the television screen.

### CHARACTER ASSETS
- ID: char_gene
  Name: Gene
  Visual: Balding middle-aged man with a mustache and thick glasses; anxious, mechanical movements; lives in monochrome.
  Clothing: Plain bakery attire with apron; drab winter coat; thick rectangular eyeglasses; neutral tones.
  Personality: Paranoid, hyper-vigilant, withdrawn; routine-bound; exhausted yet careful.
  Backstory: Lives under an alias, hiding from a vibrant past connected to Saul Goodman; keeps low profile working at a mall bakery.
  
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_gene_kneads_nervously",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "MCU",
          "angle": "high",
          "movement": "slow_dolly_in"
        },
        "lighting": "harsh fluorescent high-contrast",
        "environment_id": "loc_int_mall_bakery_kitchen",
        "entities": [
          {
            "asset_id": "char_gene",
            "position": "center_fg",
            "action_state": "kneading_dough_eyes_darting"
          },
          {
            "asset_id": "prop_bakery_dough",
            "position": "center_fg",
            "action_state": "being_kneaded"
          },
          {
            "asset_id": "prop_industrial_mixer",
            "position": "background_right",
            "action_state": "idle"
          }
        ],
        "consistency_constraints": [
          "FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements",
          "COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV",
          "LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow",
          "SEASON: Winter snowstorm",
          "Gene must wear plain bakery attire with apron.",
          "No exterior windows or weather visible from kitchen.",
          "Maintain monochrome; no color accents in kitchen equipment or surfaces."
        ]
      }
    },
    {
      "shot_id": "shot_02_returns_snowbound_home",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "LS",
          "angle": "eye_level",
          "movement": "static"
        },
        "lighting": "near-dark apartment with faint snow-muted spill from doorway",
        "environment_id": "loc_int_gene_apartment",
        "entities": [
          {
            "asset_id": "char_gene",
            "position": "frame_left",
            "action_state": "entering_and_closing_door"
          },
          {
            "asset_id": "prop_worn_out_couch",
            "position": "background_right",
            "action_state": "idle"
          },
          {
            "asset_id": "prop_television",
            "position": "background_center",
            "action_state": "screen_off"
          }
        ],
        "consistency_constraints": [
          "FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements",
          "COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV",
          "LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow",
          "SEASON: Winter snowstorm",
          "Before TV is on, room must remain very dim; TV screen must be dark.",
          "Imply heavy snowstorm via wet coat/trace snow on shoulders; never show sunny exterior."
        ]
      }
    },
    {
      "shot_id": "shot_03_sinks_inserts_vhs",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "OTS",
          "angle": "eye_level",
          "movement": "rack_focus"
        },
        "lighting": "low-key apartment; pre-TV darkness; minimal practical bounce",
        "environment_id": "loc_int_gene_apartment",
        "entities": [
          {
            "asset_id": "char_gene",
            "position": "foreground_left",
            "action_state": "leaning_forward_inserting_tape"
          },
          {
            "asset_id": "prop_vhs_tape",
            "position": "center_fg",
            "action_state": "being_inserted"
          },
          {
            "asset_id": "prop_vcr",
            "position": "center_fg",
            "action_state": "tray_open_ready"
          },
          {
            "asset_id": "prop_worn_out_couch",
            "position": "background_left",
            "action_state": "sagging"
          }
        ],
        "consistency_constraints": [
          "FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements",
          "COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV",
          "LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow",
          "SEASON: Winter snowstorm",
          "No colored practicals or LEDs visible; retain monochrome before TV powers up.",
          "Keep shot constrained to hands/VCR — Gene’s face may be partially visible as shoulder/cheek only."
        ]
      }
    },
    {
      "shot_id": "shot_04_tv_color_burst",
      "staging_layer": {
        "duration_seconds": 2.8,
        "camera": {
          "shot_scale": "MS",
          "angle": "eye_level",
          "movement": "slow_dolly_in"
        },
        "lighting": "TV glow in darkness; isolated saturated color spill in otherwise monochrome room",
        "environment_id": "loc_int_gene_apartment",
        "entities": [
          {
            "asset_id": "prop_television",
            "position": "center_fg",
            "action_state": "screen_blooming_color"
          },
          {
            "asset_id": "prop_vcr",
            "position": "foreground_below",
            "action_state": "whirring_to_life"
          }
        ],
        "consistency_constraints": [
          "FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements",
          "COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV",
          "LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow",
          "SEASON: Winter snowstorm",
          "Only TV emits saturated color; all other elements remain monochrome.",
          "Keep room near-black to emphasize color burst; avoid any competing light sources."
        ]
      }
    },
    {
      "shot_id": "shot_05_saul_ad_shouts",
      "staging_layer": {
        "duration_seconds": 4.5,
        "camera": {
          "shot_scale": "CU",
          "angle": "eye_level",
          "movement": "static"
        },
        "lighting": "TV glow key lighting; surrounding room remains dark monochrome",
        "environment_id": "loc_int_gene_apartment",
        "entities": [
          {
            "asset_id": "prop_television",
            "position": "center_fg",
            "action_state": "displaying_saul_ad"
          },
          {
            "asset_id": "char_saul_goodman",
            "position": "center_screen",
            "action_state": "pointing_and_delivering_pitch"
          }
        ],
        "consistency_constraints": [
          "FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements",
          "COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV",
          "LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow",
          "SEASON: Winter snowstorm",
          "Saul Goodman must appear in flashy suit with bright tie within TV frame only.",
          "No camera reflections or moiré on the CRT; keep screen crisp; color restricted to TV content."
        ]
      }
    },
    {
      "shot_id": "shot_06_gene_watches_silently",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "MCU",
          "angle": "eye_level",
          "movement": "slow_dolly_in"
        },
        "lighting": "colorful TV glow washing Gene’s face against deep monochrome shadows",
        "environment_id": "loc_int_gene_apartment",
        "entities": [
          {
            "asset_id": "char_gene",
            "position": "center_fg",
            "action_state": "watching_tv_silent"
          }
        ],
        "consistency_constraints": [
          "FORBIDDEN: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements",
          "COLOR_PALETTE: High-contrast black and white with isolated saturated color from TV",
          "LIGHTING: Harsh fluorescent in bakery; dim apartment lit by TV glow",
          "SEASON: Winter snowstorm",
          "Color wash on Gene’s face must be motivated solely by TV; no other light sources.",
          "Background must stay near-black; do not lift shadows."
        ]
      }
    }
  ]
}
```
