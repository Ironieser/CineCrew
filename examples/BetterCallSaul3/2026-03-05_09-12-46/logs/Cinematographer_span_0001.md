# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 93be579204aa4a52
- **Session ID**: dataset_BetterCallSaul3_2026-03-05_09-12-46
- **Timestamp**: 2026-03-05 09:15:05
- **Duration**: 50.35s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 5220
- **completion_tokens**: 10325
- **total_tokens**: 15545

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
  - LOCATION LOCK: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, 
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_saul_drives_street",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "LS",
          "angle": "eye_level",
          "movement": "handheld_tracking_parallel"
        },
        "lighting": "high-noon harsh sunlight",
        "environment_id": "loc_ext_sun_baked_street",
        "entities": [
          {
            "asset_id": "prop_battered_yellow_compact_car",
            "position": "center_fg",
            "action_state": "moving_left_to_right"
          },
          {
            "asset_id": "char_saul",
            "position": "seated_center",
            "action_state": "driving_forward"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)",
          "ERA LOCK: Contemporary (2020s) — summer, midday (NOT historical period)",
          "FORBIDDEN: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood, Payphones, CRT monitors, VHS camcorders, cassette recorders, Flip phones, Quiet suburban cul-de-sac, picket-fence neighborhoods, Skyscraper downtown canyon (e.g., Manhattan), Historical costumes or mid-century wardrobes, Snow-capped mountains visible nearby, Palm-lined boulevards and tropical vegetation, Rural dirt road or farm setting",
          "COLOR_PALETTE: sun-bleached warm tones, hard mid-day contrast, asphalt grays",
          "LIGHTING: high noon, harsh direct sunlight, short shadows, heat shimmer",
          "ARCHITECTURE: Southwestern US low-rise commercial strip: stucco, brick, chain storefronts, parking lot edges",
          "ENVIRONMENT: dry inland urban street, clear sky, heat haze",
          "VEHICLES: contemporary US sedans/SUVs (2015–2026), US license plates",
          "WARDROBE: summer streetwear: t-shirts, shorts, skate shoes, caps",
          "PROPS: modern skateboards, smartphones",
          "SIGNAGE_LANGUAGE: English primary; bilingual English/Spanish acceptable",
          "CAMERA_STYLE: handheld, kinetic, aggressive framings, chaotic coverage",
          "TONE: confrontational, darkly comedic, chaotic",
          "SOUND_DESIGN: street noise, heated shouting, skateboard wheels on asphalt; no sirens",
          "GEOGRAPHY: Albuquerque, New Mexico, USA",
          "STREET_TYPE: wide sun-baked arterial with strip-mall frontage, minimal shade",
          "DAY_PART: midday (12–2pm), peak summer heat",
          "Windshield intact — no shatter yet",
          "Battered yellow compact car with one red door visible"
        ]
      }
    },
    {
      "shot_id": "shot_02_teen_smashes_windshield",
      "staging_layer": {
        "duration_seconds": 2.0,
        "camera": {
          "shot_scale": "POV",
          "angle": "eye_level",
          "movement": "handheld_jolt"
        },
        "lighting": "high-noon harsh sunlight",
        "environment_id": "loc_ext_sun_baked_street",
        "entities": [
          {
            "asset_id": "char_teen_scammer",
            "position": "center_fg",
            "action_state": "colliding_with_windshield"
          },
          {
            "asset_id": "prop_shattered_windshield",
            "position": "center_fg",
            "action_state": "shattering_on_impact"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)",
          "ERA LOCK: Contemporary (2020s) — summer, midday (NOT historical period)",
          "FORBIDDEN: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood, Payphones, CRT monitors, VHS camcorders, cassette recorders, Flip phones, Quiet suburban cul-de-sac, picket-fence neighborhoods, Skyscraper downtown canyon (e.g., Manhattan), Historical costumes or mid-century wardrobes, Snow-capped mountains visible nearby, Palm-lined boulevards and tropical vegetation, Rural dirt road or farm setting",
          "COLOR_PALETTE: sun-bleached warm tones, hard mid-day contrast, asphalt grays",
          "LIGHTING: high noon, harsh direct sunlight, short shadows, heat shimmer",
          "ARCHITECTURE: Southwestern US low-rise commercial strip: stucco, brick, chain storefronts, parking lot edges",
          "ENVIRONMENT: dry inland urban street, clear sky, heat haze",
          "VEHICLES: contemporary US sedans/SUVs (2015–2026), US license plates",
          "WARDROBE: summer streetwear: t-shirts, shorts, skate shoes, caps",
          "PROPS: modern skateboards, smartphones",
          "SIGNAGE_LANGUAGE: English primary; bilingual English/Spanish acceptable",
          "CAMERA_STYLE: handheld, kinetic, aggressive framings, chaotic coverage",
          "TONE: confrontational, darkly comedic, chaotic",
          "SOUND_DESIGN: street noise, heated shouting, skateboard wheels on asphalt; no sirens",
          "GEOGRAPHY: Albuquerque, New Mexico, USA",
          "STREET_TYPE: wide sun-baked arterial with strip-mall frontage, minimal shade",
          "DAY_PART: midday (12–2pm), peak summer heat",
          "Show impact moment — teen and shattered windshield visible",
          "Interior POV from Saul — Saul not visible",
          "Shattered windshield continuity begins"
        ]
      }
    },
    {
      "shot_id": "shot_03_teen_screams_extortion",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "MS",
          "angle": "eye_level",
          "movement": "handheld_slight_push_in"
        },
        "lighting": "high-noon harsh sunlight",
        "environment_id": "loc_ext_sun_baked_street",
        "entities": [
          {
            "asset_id": "char_teen_scammer",
            "position": "center_fg",
            "action_state": "clutching_leg_screaming"
          },
          {
            "asset_id": "char_scammer_friend",
            "position": "frame_right",
            "action_state": "filming_with_smartphone"
          },
          {
            "asset_id": "prop_smartphone",
            "position": "frame_right",
            "action_state": "recording"
          },
          {
            "asset_id": "prop_battered_yellow_compact_car",
            "position": "background_left",
            "action_state": "stopped_at_roadside"
          },
          {
            "asset_id": "prop_shattered_windshield",
            "position": "background_left",
            "action_state": "visible_shattered"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)",
          "ERA LOCK: Contemporary (2020s) — summer, midday (NOT historical period)",
          "FORBIDDEN: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood, Payphones, CRT monitors, VHS camcorders, cassette recorders, Flip phones, Quiet suburban cul-de-sac, picket-fence neighborhoods, Skyscraper downtown canyon (e.g., Manhattan), Historical costumes or mid-century wardrobes, Snow-capped mountains visible nearby, Palm-lined boulevards and tropical vegetation, Rural dirt road or farm setting",
          "COLOR_PALETTE: sun-bleached warm tones, hard mid-day contrast, asphalt grays",
          "LIGHTING: high noon, harsh direct sunlight, short shadows, heat shimmer",
          "ARCHITECTURE: Southwestern US low-rise commercial strip: stucco, brick, chain storefronts, parking lot edges",
          "ENVIRONMENT: dry inland urban street, clear sky, heat haze",
          "VEHICLES: contemporary US sedans/SUVs (2015–2026), US license plates",
          "WARDROBE: summer streetwear: t-shirts, shorts, skate shoes, caps",
          "PROPS: modern skateboards, smartphones",
          "SIGNAGE_LANGUAGE: English primary; bilingual English/Spanish acceptable",
          "CAMERA_STYLE: handheld, kinetic, aggressive framings, chaotic coverage",
          "TONE: confrontational, darkly comedic, chaotic",
          "SOUND_DESIGN: street noise, heated shouting, skateboard wheels on asphalt; no sirens",
          "GEOGRAPHY: Albuquerque, New Mexico, USA",
          "STREET_TYPE: wide sun-baked arterial with strip-mall frontage, minimal shade",
          "DAY_PART: midday (12–2pm), peak summer heat",
          "Shattered windshield visible on car in background",
          "Smartphone filming clearly visible",
          "Teen clutches leg on hot asphalt",
          "At least one skateboard near teen or friend if visible"
        ]
      }
    },
    {
      "shot_id": "shot_04_saul_storms_out",
      "staging_layer": {
        "duration_seconds": 2.5,
        "camera": {
          "shot_scale": "MLS",
          "angle": "low",
          "movement": "handheld_follow"
        },
        "lighting": "high-noon harsh sunlight",
        "environment_id": "loc_ext_sun_baked_street",
        "entities": [
          {
            "asset_id": "char_saul",
            "position": "frame_left",
            "action_state": "striding_forward_raging"
          },
          {
            "asset_id": "prop_battered_yellow_compact_car",
            "position": "background_left",
            "action_state": "driver_door_open"
          },
          {
            "asset_id": "char_teen_scammer",
            "position": "frame_right_midground",
            "action_state": "on_ground_looking_up"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)",
          "ERA LOCK: Contemporary (2020s) — summer, midday (NOT historical period)",
          "FORBIDDEN: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood, Payphones, CRT monitors, VHS camcorders, cassette recorders, Flip phones, Quiet suburban cul-de-sac, picket-fence neighborhoods, Skyscraper downtown canyon (e.g., Manhattan), Historical costumes or mid-century wardrobes, Snow-capped mountains visible nearby, Palm-lined boulevards and tropical vegetation, Rural dirt road or farm set
...
```
