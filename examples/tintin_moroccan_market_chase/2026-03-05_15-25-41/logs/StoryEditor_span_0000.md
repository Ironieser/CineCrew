# Agent: StoryEditor
- **Span ID**: span_0000
- **Trace ID**: 2bdd77fb27b84af1
- **Session ID**: dataset_tintin_moroccan_market_chase_2026-03-05_15-25-41
- **Timestamp**: 2026-03-05 15:27:02
- **Duration**: 49.91s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3061
- **completion_tokens**: 3959
- **total_tokens**: 7020

## Input (preview)

```
In a sweeping, high-speed tracking shot through a vibrant, sun-baked Moroccan market, a young reporter with a signature quiff speeds forward on a vintage motorcycle with a sidecar. His bearded companion sits in the sidecar, wildly aiming a bazooka. They crash violently through colorful fruit stands, sending oranges flying directly into the lens. As the motorcycle launches into the air off a ramp of debris, the companion accidentally fires the weapon. A massive explosion hits a distant dam, and i...
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
- **LOCATION LOCK**: Moroccan market district, North Africa (NOT European city)
- **ERA LOCK**: Daytime chase, contemporary with vintage tech
- **FORBIDDEN ELEMENTS**: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage
- **STYLE OVERRIDES**:
  * color_palette: warm ochres, terracotta, bright produce colors, sun-bleached neutrals
  * architecture: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks
  * lighting: harsh midday sun, hard shadows, dusty air bloom

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Moroccan market district, North Africa (NOT European city)
  - ERA LOCK: Daytime chase, contemporary with vintage tech
  - FORBIDDEN: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage
  - COLOR_PALETTE: warm ochres, terracotta, bright produce colors, sun-bleached neutrals
  - ARCHITECTURE: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks
  - LIGHTING: harsh midday sun, hard shadows, dusty air bloom
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Midday; contemporary adventure with retro elements
Global Mood: Frenetic, high-stakes, catastrophic, kinetic
Key Events: High-speed tracking shot through a Moroccan market, Bearded companion aims a bazooka from the sidecar during the chase, Motorcycle smashes through fruit stands; oranges fly into the lens, Bike launches off a ramp of debris, Accidental bazooka discharge, Explosion strikes a distant dam, Floodwater surges into narrow streets, sweeping away the market
Cultural Context: North African medina-style marketplace: bustling vendors, colorful produce, sun-baked environment and tight alleyways.

### GLOBAL VISUAL STYLE
High-energy adventure with sun-baked North African palette, saturated colors, kinetic camera, practical stunts, comedic panic amid real danger, stylized realism.

### CHARACTER ASSETS
- ID: char_young_reporter
  Name: Young Reporter
  Visual: Young male reporter with a signature quiff, lithe build, agile rider; dust-streaked, focused eyes.
  Clothing: Light shirt, rolled sleeves, trousers, leather boots, goggles; minimal gear.
  Personality: Brave, quick-thinking, resourceful, relentless under pressure.
  Backstory: A roving journalist chasing scoops across continents; adept motorcyclist; often entangled in dangerous capers.
  Motivation: Outrun the flood, protect his companion, and survive to report the story.
- ID: char_bearded_companion
  Name: Bearded Companion
  Visual: Rugged, bearded man of sturdy build in the sidecar; frantic, aiming a bazooka; dust-covered.
  Clothing: Utility jacket, trousers, boots; protective goggles; rugged accessories.
  Personality: Impulsive, loyal, brave; comedic panic under stress.
  Backstory: Seasoned adventurer and fixer; accompanies the reporter on risky pursuits; more brawn than finesse.
  Motivation: Escape the market alive, control the weapon, stick with the reporter.

### LOCATION ASSETS
- ID: loc_ext_moroccan_market
  Name: Moroccan Market (EXT)
  Visual: Sun-baked, crowded alleys, colorful 
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_reporter_blazes_market",
      "narrative_layer": {
        "narrative_action": "The young reporter races through the Moroccan market on a vintage motorcycle as his bearded companion in the sidecar wildly aims a bazooka.",
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
      "shot_id": "shot_02_fruit_stands_explode",
      "narrative_layer": {
        "narrative_action": "The motorcycle smashes through colorful fruit stands, blasting crates open and sending oranges flying toward the lens.",
        "emotional_beat": "chaos_escalates",
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
      "shot_id": "shot_03_bike_launches_debris",
      "narrative_layer": {
        "narrative_action": "The motorcycle hits a makeshift debris ramp and launches into the air over the cluttered alley.",
        "emotional_beat": "suspense_peaks",
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
      "shot_id": "shot_04_bazooka_accidental_fire",
      "narrative_layer": {
        "narrative_action": "Midair, the bearded companion accidentally fires the bazooka from the sidecar.",
        "emotional_beat": "sudden_shock",
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
      "shot_id": "shot_05_dam_explosion_boom",
      "narrative_layer": {
        "narrative_action": "A massive explosion strikes the distant dam, sending a plume up from its concrete face.",
        "emotional_beat": "catastrophe_triggered",
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
      "shot_id": "shot_06_flood_surge_pursues",
      "narrative_layer": {
        "narrative_action": "A towering wall of floodwater surges into the narrow market streets right behind them, sweeping stalls and debris in its wake.",
        "emotional_beat": "catastrophe_unleashed",
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
