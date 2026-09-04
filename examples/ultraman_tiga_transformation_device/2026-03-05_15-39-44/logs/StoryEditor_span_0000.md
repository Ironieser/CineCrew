# Agent: StoryEditor
- **Span ID**: span_0000
- **Trace ID**: 3117a8ab38794c6e
- **Session ID**: dataset_ultraman_tiga_transformation_device_2026-03-05_15-39-44
- **Timestamp**: 2026-03-05 15:41:37
- **Duration**: 69.22s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3423
- **completion_tokens**: 5182
- **total_tokens**: 8605

## Input (preview)

```
Shot from a low, slightly wide angle, a determined young man in a red-and-white sci-fi uniform stands against a blurred background. His eyes lock onto the camera with intense resolve. He pulls a white, intricate device from his jacket and thrusts it high into the air. With a sharp mechanical snap, the twin crystal wings at the top of the device spring open. Instantly, an overwhelmingly brilliant, pure white light erupts from the center crystal. The harsh, divine glow completely washes over his f...
```

## Prompt Rendered

```
=== System ===
You are a Story Analyst / Script Supervisor.
Your single responsibility: read the script segment and break it into
individual SHOTS, then fill the narrative_layer for each shot.

You do NOT decide how to shoot (no camera specs, no lighting, no positions).
That is the Cinematographer's job.

=========================================================
YOUR OUTPUT CONTRACT
=========================================================
Return a JSON object with one key "shots":
{
  "shots": [
    {
      "shot_id": "shot_01_<3-word-slug>",
      "narrative_layer": { ... }
    },
    ...
  ]
}

narrative_layer fields:
  - narrative_action (str):
      What physically happens in this shot. One clear sentence.
      Focus on observable action, not subtext.
      Example: "Michael enters the diner and sits across from Sollozzo."

  - emotional_beat (str):
      The dominant emotional shift/arc within this single shot.
      Use compact labels like "rising_tension", "grief_restrained",
      "false_calm", "defiant_resolve", "quiet_dread".
      One label is enough; avoid vague terms like "dramatic" or "intense".

  - dialogue:
      - has_dialogue (bool): true only when a character speaks aloud.
      - speaker_asset_id (str|null):
          MUST be a char_xxx ID from Asset Context. null if no dialogue.
      - listener_asset_id (str|null):
          char_xxx ID of the primary listener, or "group", or null.
      - text (str|null):
          Verbatim dialogue from the script. null if no dialogue.
      - voice_preset (str|null):
          voice_preset_id from AssetLibrary if known; otherwise null.

=========================================================
SHOT BOUNDARY RULES
=========================================================
Create a NEW shot when ANY of the following occurs:
  1. A new character enters or exits the frame.
  2. The speaker changes in dialogue-heavy scenes.
  3. A clear narrative beat ends (e.g., confrontation → silence).
  4. Time passes (even briefly — a cut implies time passage).
Do NOT split on every line of dialogue — group related lines into one shot.

=========================================================
CRITICAL RULES
=========================================================
1. speaker_asset_id / listener_asset_id MUST come from Asset Context below.
   NEVER invent character IDs.
2. Dialogue text should be verbatim from the script.
3. Do NOT add any camera, lighting, framing, or position information.
4. shot_id format: "shot_01_slug", "shot_02_slug", etc. (zero-padded index + 3-word slug).



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
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)
  - ERA LOCK: Unspecified far-future sci-fi era (NOT contemporary or historical)
  - FORBIDDEN: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacuum tubes), Military insignia, firearms, tactical gear, Contemporary brand logos, text signage, or readable UI text, Lush natural scenery in clear focus (trees, mountains, oceans), Space vistas or 
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_intense_gaze_holds",
      "narrative_layer": {
        "narrative_action": "A determined young man fixes his eyes directly toward the camera with intense resolve against a blurred background.",
        "emotional_beat": "defiant_resolve",
        "dialogue": {
          "has_dialogue": false,
          "speaker_asset_id": null,
          "listener_asset_id": null,
          "text": null,
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_02_draws_device_high",
      "narrative_layer": {
        "narrative_action": "He pulls a white, intricate device from his jacket and thrusts it high into the air.",
        "emotional_beat": "decisive_action",
        "dialogue": {
          "has_dialogue": false,
          "speaker_asset_id": null,
          "listener_asset_id": null,
          "text": null,
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_03_crystal_wings_open",
      "narrative_layer": {
        "narrative_action": "With a sharp mechanical snap, the device’s twin crystal wings spring open.",
        "emotional_beat": "activation_release",
        "dialogue": {
          "has_dialogue": false,
          "speaker_asset_id": null,
          "listener_asset_id": null,
          "text": null,
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_04_white_light_erupts",
      "narrative_layer": {
        "narrative_action": "An overwhelmingly brilliant pure white light erupts from the device’s center crystal, washing over his face and blowing out the exposure.",
        "emotional_beat": "overwhelming_awe",
        "dialogue": {
          "has_dialogue": false,
          "speaker_asset_id": null,
          "listener_asset_id": null,
          "text": null,
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_05_frame_swallowed_white",
      "narrative_layer": {
        "narrative_action": "The blinding white light rapidly swallows the entire frame.",
        "emotional_beat": "total_whiteout",
        "dialogue": {
          "has_dialogue": false,
          "speaker_asset_id": null,
          "listener_asset_id": null,
          "text": null,
          "voice_preset": null
        }
      }
    }
  ]
}
```
