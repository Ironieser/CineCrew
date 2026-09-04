# Agent: StoryEditor
- **Span ID**: span_0000
- **Trace ID**: 26897c809d8e48bb
- **Session ID**: dataset_iron_man_cave_forging_mask_2026-03-05_15-46-17
- **Timestamp**: 2026-03-05 15:47:59
- **Duration**: 30.07s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3649
- **completion_tokens**: 4595
- **total_tokens**: 8244

## Input (preview)

```
Deep inside a dark, gritty cave, the only light source is the fierce, dancing orange glow of a raging forge fire. A muscular man, covered in sweat and soot, wearing a grimy grey tank top, stands over a heavy steel anvil. With intense physical exertion, he raises a massive iron hammer and strikes a glowing, red-hot metal mask. Clang! Every brutal strike sends a massive, bright shower of orange sparks spraying violently across the dark frame, briefly and dramatically illuminating his exhausted, so...
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

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Subterranean cave forge, undetermined locale — DO NOT infer or depict a specific country, culture, or fantasy realm (NOT medieval Europe, NOT feudal Japan, NOT Norse, NOT dwarven/Tolkien).
  - ERA LOCK: Atemporal, era-agnostic underground workshop — no overt historical markers (NOT medieval, NOT steampunk, NOT cyberpunk, NOT futuristic sci‑fi).
  - FORBIDDEN: Medieval castle architecture, Viking/Norse runes, Celtic knotwork, Samurai armor, kabuto, katana, Torii gates, Gothic arches or stained glass, Art Deco motifs, Roman columns or Greek statues, Renaissance paintings, Fantasy dwarven halls (Moria style), Elven motifs, Steampunk gears and brass g
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_forge_fire_glows",
      "narrative_layer": {
        "narrative_action": "The blacksmith stands over the anvil in the dark cave as the raging forge fire casts the only light.",
        "emotional_beat": "quiet_dread",
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
      "shot_id": "shot_02_hammer_raised_high",
      "narrative_layer": {
        "narrative_action": "With intense exertion, the blacksmith heaves the massive iron hammer up and poises it above the glowing metal mask on the anvil.",
        "emotional_beat": "rising_tension",
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
      "shot_id": "shot_03_sparks_violently_erupt",
      "narrative_layer": {
        "narrative_action": "He slams the hammer onto the red-hot mask, blasting a shower of bright orange sparks that briefly reveal his exhausted, soot-stained face.",
        "emotional_beat": "explosive_release",
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
