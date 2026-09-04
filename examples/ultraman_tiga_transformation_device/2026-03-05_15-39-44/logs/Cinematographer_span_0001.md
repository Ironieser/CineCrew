# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 3117a8ab38794c6e
- **Session ID**: dataset_ultraman_tiga_transformation_device_2026-03-05_15-39-44
- **Timestamp**: 2026-03-05 15:42:16
- **Duration**: 38.30s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4488
- **completion_tokens**: 5998
- **total_tokens**: 10486

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
- **LOCATION LOCK**: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)
- **ERA LOCK**: Unspecified far-future sci-fi era (NOT contemporary or historical)
- **FORBIDDEN ELEMENTS**: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacuum tubes), Military insignia, firearms, tactical gear, Contemporary brand logos, text signage, or readable UI text, Lush natural scenery in clear focus (trees, mountains, oceans), Space vistas or starfields; keep environment non-cosmic and abstract, Neon cyberpunk street scenes (wet asphalt, kanji signage, crowded alleys), Rustic materials (wood beams, stone walls), Warm candlelight or firelight; avoid mystical ritual props (candles, incense), Brown/earthy, grungy palettes that detract from high-key white purity
- **STYLE OVERRIDES**:
  * color_palette: High-key whites, cool grays, subtle iridescent crystal highlights
  * materials: Polished matte white composites, clear/crystal elements, minimal metal
  * lighting: Pure white core eruption with exposure blowout and soft cinematic bloom; sharp mechanical snap cue
  * architecture: Non-descript abstract futurist forms; no identifiable cultural motifs or signage
  * camera_style: Front-facing hero close-up, shallow depth-of-field, blurred background
  * props: White intricate activation device with twin crystal wings (crystal/mechanical aesthetic)
  * wardrobe: Modern-futurist jacket; no logos, patches, or military insignia
  * vfx: Clean geometric light behaviors; no glyphs, runes, smoke, or particle clutter
  * ui_elements: Avoid textual HUD; if needed, use minimal geometric overlays only
  * environment: Indeterminate interior or staging area implied; maintain abstraction

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST con
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_intense_gaze_holds",
      "staging_layer": {
        "duration_seconds": 2.8,
        "camera": {
          "shot_scale": "CU",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "high-key white soft fill with shallow depth-of-field; background blurred",
        "environment_id": "loc_unknown_blurred_background",
        "entities": [
          {
            "asset_id": "char_determined_young_man",
            "position": "center_fg",
            "action_state": "locking_gaze_to_camera"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)",
          "ERA LOCK: Unspecified far-future sci-fi era (NOT contemporary or historical)",
          "FORBIDDEN: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacuum tubes), Military insignia, firearms, tactical gear, Contemporary brand logos, text signage, or readable UI text, Lush natural scenery in clear focus (trees, mountains, oceans), Space vistas or starfields; keep environment non-cosmic and abstract, Neon cyberpunk street scenes (wet asphalt, kanji signage, crowded alleys), Rustic materials (wood beams, stone walls), Warm candlelight or firelight; avoid mystical ritual props (candles, incense), Brown/earthy, grungy palettes that detract from high-key white purity",
          "COLOR_PALETTE: High-key whites, cool grays, subtle iridescent crystal highlights",
          "MATERIALS: Polished matte white composites, clear/crystal elements, minimal metal",
          "LIGHTING: Pure white core eruption with exposure blowout and soft cinematic bloom; sharp mechanical snap cue",
          "ARCHITECTURE: Non-descript abstract futurist forms; no identifiable cultural motifs or signage",
          "CAMERA_STYLE: Front-facing hero close-up, shallow depth-of-field, blurred background",
          "PROPS: White intricate activation device with twin crystal wings (crystal/mechanical aesthetic)",
          "WARDROBE: Modern-futurist jacket; no logos, patches, or military insignia",
          "VFX: Clean geometric light behaviors; no glyphs, runes, smoke, or particle clutter",
          "UI_ELEMENTS: Avoid textual HUD; if needed, use minimal geometric overlays only",
          "ENVIRONMENT: Indeterminate interior or staging area implied; maintain abstraction",
          "Shot-specific: Maintain shallow depth of field and blurred, non-descript background; no readable text or signage in frame"
        ]
      }
    },
    {
      "shot_id": "shot_02_draws_device_high",
      "staging_layer": {
        "duration_seconds": 3.2,
        "camera": {
          "shot_scale": "MS",
          "angle": "low",
          "movement": "tilt_up_follow"
        },
        "lighting": "cool high-key whites with soft fill; crisp rim and specular on raised device",
        "environment_id": "loc_unknown_blurred_background",
        "entities": [
          {
            "asset_id": "char_determined_young_man",
            "position": "frame_center",
            "action_state": "drawing_device_and_thrusting_up"
          },
          {
            "asset_id": "prop_transformation_device",
            "position": "frame_top_center",
            "action_state": "held_raised_high"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)",
          "ERA LOCK: Unspecified far-future sci-fi era (NOT contemporary or historical)",
          "FORBIDDEN: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacuum tubes), Military insignia, firearms, tactical gear, Contemporary brand logos, text signage, or readable UI text, Lush natural scenery in clear focus (trees, mountains, oceans), Space vistas or starfields; keep environment non-cosmic and abstract, Neon cyberpunk street scenes (wet asphalt, kanji signage, crowded alleys), Rustic materials (wood beams, stone walls), Warm candlelight or firelight; avoid mystical ritual props (candles, incense), Brown/earthy, grungy palettes that detract from high-key white purity",
          "COLOR_PALETTE: High-key whites, cool grays, subtle iridescent crystal highlights",
          "MATERIALS: Polished matte white composites, clear/crystal elements, minimal metal",
          "LIGHTING: Pure white core eruption with exposure blowout and soft cinematic bloom; sharp mechanical snap cue",
          "ARCHITECTURE: Non-descript abstract futurist forms; no identifiable cultural motifs or signage",
          "CAMERA_STYLE: Front-facing hero close-up, shallow depth-of-field, blurred background",
          "PROPS: White intricate activation device with twin crystal wings (crystal/mechanical aesthetic)",
          "WARDROBE: Modern-futurist jacket; no logos, patches, or military insignia",
          "VFX: Clean geometric light behaviors; no glyphs, runes, smoke, or particle clutter",
          "UI_ELEMENTS: Avoid textual HUD; if needed, use minimal geometric overlays only",
          "ENVIRONMENT: Indeterminate interior or staging area implied; maintain abstraction",
          "Shot-specific: Keep background fully abstract and blurred; ensure jacket remains logo-free; device remains pristine white with crystal elements; no textual overlays"
        ]
      }
    },
    {
      "shot_id": "shot_03_crystal_wings_open",
      "staging_layer": {
        "duration_seconds": 2.2,
        "camera": {
          "shot_scale": "ECU",
          "angle": "eye_level",
          "movement": "rack_focus"
        },
        "lighting": "crisp white accent on device; specular highlights on crystal wings; pre-eruption mechanical snap moment",
        "environment_id": "loc_unknown_blurred_background",
        "entities": [
          {
            "asset_id": "prop_transformation_device",
            "position": "center_fg",
            "action_state": "wings_snap_open"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)",
          "ERA LOCK: Unspecified far-future sci-fi era (NOT contemporary or historical)",
          "FORBIDDEN: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacuum tubes), Military insignia, firearms, tactical gear, Contemporary brand logos, text signage, or readable UI text, Lush natural scenery in clear focus (trees, mountains, oceans), Space vistas or starfields; keep environment non-cosmic and abstract, Neon cyberpunk street scenes (wet asphalt, kanji signage, crowded alleys), Rustic materials (wood beams, stone walls), Warm candlelight or firelight; avoid mystical ritual props (candles, incense), Brown/earthy, grungy palettes that detract from high-key white purity",
          "COLOR_PALETTE: High-key whites, cool grays, subtle iridescent crystal highlights",
          "MATERIALS: Polished matte white composites, clear/crystal elements, minimal metal",
          "LIGHTING: Pure white core eruption with exposure blowout and soft cinematic bloom; sharp mechanical snap cue",
          "ARCHITECTURE: Non-descript abstract futurist forms; no identifiable cultural motifs or signage",
          "CAMERA_STYLE: Front-facing hero close-up, shallow depth-of-field, blurred background",
          "PROPS: White intricate activation device with twin crystal wings (crystal/mechanical aesthetic)",
          "WARDROBE: Modern-futurist jacket; no logos, patches, or military insignia",
          "VFX: Clean geometric light behaviors; no glyphs, runes, smoke, or particle clutter",
          "UI_ELEMENTS: Avoid textual HUD; if needed, use minimal geometric overlays only",
          "ENVIRONMENT: Indeterminate interior or staging area implied; maintain abstraction",
          "Shot-specific: Emphasize mechanical snap visually; no glyphs, runes, smoke, or text; maintain shallow DOF with blurred background"
        ]
      }
    },
    {
      "shot_id": "shot_04_white_light_erupts",
      "staging_layer": {
        "duration_seconds": 3.6,
        "camera": {
          "shot_scale": "CU",
          "angle": "low",
          "movement": "static"
        },
        "lighting": "pure white core eruption with exposure blowout and soft cinematic bloom; face wash with wrap-around highlights",
        "environment_id": "loc_unknown_blurred_background",
        "entities": [
          {
            "asset_id": "char_determined_young_man",
            "position": "center_fg",
            "action_state": "flooded_by_light"
          },
          {
            "asset_id": "prop_transformation_device",
            "position": "frame_right_fg",
            "action_state": "emitting_core_light"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)",
          "ERA LOCK: Unspecified far-future sci-fi era (NOT contemporary or historical)",
          "FORBIDDEN: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacuum tubes), Military insignia, firearms, tactical gear, Contemporary brand logos, text signage, or readable UI text, Lush natural scenery in clear focus (trees, mountains, oceans), Space vistas or starfields; keep environment non-cosmic and abstract, Neon cyberpunk street scenes (wet asphalt, kanji signage, crowded alleys), Rustic materials (wood beams, stone walls), Warm candlelight or firelight; avoid mystical ritual props (candles, incense), Brown/earthy, grungy palettes that detract from high-key white purity",
          "COLOR_PALETTE: High-key whites, cool grays, subtle iridescent crystal highlights",
          "MATERIALS: Polished matte white composites, clear/crystal elements, minimal metal",
          "LIGHTING: Pure white core eruption with exposure blowout and soft cinematic bloom; sharp mechanical snap cue",
          "ARCHITECTURE: Non-descript abstract futurist forms; no identifiable cultural mot
...
```
