# Agent: StoryEditor
- **Span ID**: span_0000
- **Trace ID**: 93be579204aa4a52
- **Session ID**: dataset_BetterCallSaul3_2026-03-05_09-12-46
- **Timestamp**: 2026-03-05 09:14:15
- **Duration**: 37.37s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3872
- **completion_tokens**: 8417
- **total_tokens**: 12289

## Input (preview)

```
On a bright, sun-baked street, Saul is driving a severely battered yellow compact car with one mismatched red door. Suddenly, a teenage skateboarder flies through the air and smashes heavily onto the car's windshield, instantly shattering the glass. The teen rolls onto the hot asphalt, clutching his leg and screaming, "My leg! You broke my leg!" while his friend rushes over with a smartphone to record the extortion attempt. Instead of panicking, Saul storms out of the car in a fit of absolute ra...
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
- **LOCATION LOCK**: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)
- **ERA LOCK**: Contemporary (2020s) — summer, midday (NOT historical period)
- **FORBIDDEN ELEMENTS**: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood, Payphones, CRT monitors, VHS camcorders, cassette recorders, Flip phones, Quiet suburban cul-de-sac, picket-fence neighborhoods, Skyscraper downtown canyon (e.g., Manhattan), Historical costumes or mid-century wardrobes, Snow-capped mountains visible nearby, Palm-lined boulevards and tropical vegetation, Rural dirt road or farm setting
- **STYLE OVERRIDES**:
  * color_palette: sun-bleached warm tones, hard mid-day contrast, asphalt grays
  * lighting: high noon, harsh direct sunlight, short shadows, heat shimmer
  * architecture: Southwestern US low-rise commercial strip: stucco, brick, chain storefronts, parking lot edges
  * environment: dry inland urban street, clear sky, heat haze
  * vehicles: contemporary US sedans/SUVs (2015–2026), US license plates
  * wardrobe: summer streetwear: t-shirts, shorts, skate shoes, caps
  * props: modern skateboards, smartphones
  * signage_language: English primary; bilingual English/Spanish acceptable
  * camera_style: handheld, kinetic, aggressive framings, chaotic coverage
  * tone: confrontational, darkly comedic, chaotic
  * sound_design: street noise, heated shouting, skateboard wheels on asphalt; no sirens
  * geography: Albuquerque, New Mexico, USA
  * street_type: wide sun-baked arterial with strip-mall frontage, minimal shade
  * day_part: midday (12–2pm), peak summer heat

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)
  - ERA LOCK: Contemporary (2020s) — summer, midday (NOT historical period)
  - FORBIDDEN: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood, Payphones, CRT monitors, VHS camcorders, cassette recorders, Flip phones, Quiet suburban cul-de-sac, picket-fence neighborhoods, Skyscraper downtown canyon (e.g., Manhattan), Historical costumes or mid-century wardrobes, Snow-capped mountains visible nearby, Palm-lined boulevards and tropical ve
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_saul_drives_street",
      "narrative_layer": {
        "narrative_action": "Saul drives his battered yellow compact car along the sun-baked street.",
        "emotional_beat": "false_calm",
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
      "shot_id": "shot_02_teen_smashes_windshield",
      "narrative_layer": {
        "narrative_action": "A teenage skateboarder flies into frame and smashes onto Saul’s windshield, shattering it.",
        "emotional_beat": "shock_impact",
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
      "shot_id": "shot_03_teen_screams_extortion",
      "narrative_layer": {
        "narrative_action": "The teen rolls onto the asphalt, clutches his leg, and screams while his friend rushes in filming.",
        "emotional_beat": "feigned_distress",
        "dialogue": {
          "has_dialogue": true,
          "speaker_asset_id": "char_teen_scammer",
          "listener_asset_id": "char_saul",
          "text": "My leg! You broke my leg!",
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_04_saul_storms_out",
      "narrative_layer": {
        "narrative_action": "Saul bursts out of the car in a rage and strides toward the teen.",
        "emotional_beat": "anger_surge",
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
      "shot_id": "shot_05_saul_kicks_knee",
      "narrative_layer": {
        "narrative_action": "Saul kicks the teen’s supposedly broken knee.",
        "emotional_beat": "brutal_reversal",
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
      "shot_id": "shot_06_saul_taunts_lawyer",
      "narrative_layer": {
        "narrative_action": "Saul faces the scammer kids and yells, mocking their hustle and declaring he is a lawyer.",
        "emotional_beat": "taunting_authority",
        "dialogue": {
          "has_dialogue": true,
          "speaker_asset_id": "char_saul",
          "listener_asset_id": "group",
          "text": "Zero point zero for choice of victim! I'm a lawyer!",
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_07_scammers_scramble_flee",
      "narrative_layer": {
        "narrative_action": "The two scammer kids drop the act, grab their skateboards, and sprint away.",
        "emotional_beat": "panic_flight",
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
      "shot_id": "shot_08_saul_shouts_check",
      "narrative_layer": {
        "narrative_action": "Saul stands beside his shattered car, points at the retreating kids, and shouts after them.",
        "emotional_beat": "triumphant_mockery",
        "dialogue": {
          "has_dialogue": true,
          "speaker_asset_id": "char_saul",
          "listener_asset_id": "group",
          "text": "I'll take a check!",
          "voice_preset": null
        }
      }
    }
  ]
}
```
