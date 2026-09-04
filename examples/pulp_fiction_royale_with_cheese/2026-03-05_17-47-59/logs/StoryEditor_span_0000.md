# Agent: StoryEditor
- **Span ID**: span_0000
- **Trace ID**: 542f92ea31d54213
- **Session ID**: dataset_pulp_fiction_royale_with_cheese_2026-03-05_17-47-59
- **Timestamp**: 2026-03-05 17:49:21
- **Duration**: 57.42s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 2823
- **completion_tokens**: 3608
- **total_tokens**: 6431

## Input (preview)

```
On a bright, sunlit 1990s Los Angeles morning, Vincent Vega and Jules Winnfield, dressed in crisp black suits, ride in the front seats of a moving vintage car. The camera is locked tightly on their faces as they casually smoke cigarettes, the shifting shadows and bright sunlight from the passing street rolling continuously across their features. They engage in a relaxed, rhythmic physical exchange of gestures and nods, completely at ease in the cramped leather interior. Over the rhythmic hum of ...
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
- **LOCATION LOCK**: Los Angeles, California, USA (NOT New York, NOT Europe)
- **ERA LOCK**: 1990s America
- **FORBIDDEN ELEMENTS**: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside
- **STYLE OVERRIDES**:
  * color_palette: Warm California morning sunlight, strong contrast
  * architecture: Automotive interior only, no exterior landmarks
  * wardrobe: Crisp black suits, white shirts, narrow ties

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Los Angeles, California, USA (NOT New York, NOT Europe)
  - ERA LOCK: 1990s America
  - FORBIDDEN: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside
  - COLOR_PALETTE: Warm California morning sunlight, strong contrast
  - ARCHITECTURE: Automotive interior only, no exterior landmarks
  - WARDROBE: Crisp black suits, white shirts, narrow ties
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: 1990s Los Angeles morning
Global Mood: Relaxed, cool, rhythmic
Key Events: Vincent Vega and Jules Winnfield ride in a moving vintage car, smoking., Jules asks a question over the engine hum and shifting light., Vincent replies in voiceover: "They call it a Royale with Cheese."
Cultural Context: 1990s American urban culture; LA car-centric life; casual fast-food pop-culture banter.

### GLOBAL VISUAL STYLE
Naturalistic 1990s neo-noir; bright Californian sunlight; tight locked close-ups; minimal palette (black suits, tan leather); rhythmic, casual pacing; emphasis on pop-culture dialogue.

### CHARACTER ASSETS
- ID: char_vincent_vega
  Name: Vincent Vega
  Visual: A man in a crisp black suit, relaxed and composed, smoking casually in a cramped leather car interior; his face catches shifting bright Los Angeles sunlight and moving street shadows.
  Clothing: Crisp black suit, white shirt, narrow tie; minimal accessories.
  Personality: Cool, detached, amiable; goes with the flow, observant, unhurried.
  Backstory: Professional partner to Jules; accustomed to casual banter during drives.
  Motivation: Share a pop-culture observation and keep the ride relaxed.
- ID: char_jules_winnfield
  Name: Jules Winnfield
  Visual: A man in a crisp black suit, expressive yet controlled, at ease in the cramped leather interior; shifting sunlight and passing shadows play across his features as he engages with rhythmic gestures.
  Clothing: Crisp black suit, white shirt, thin tie; confident posture.
  Personality: Commanding yet easygoing; curious, sharp, enjoys playful debate.
  Backstory: Works closely with Vincent; comfortable exchanging questions during drives.
  Motivation: Prompt Vincent and keep the conversation flowing.

### LOCATION ASSETS
- ID: loc_int_moving_car
  Name: Moving Car - Front Seats (INT)
  Visual: Bright California sun casting moving shadows; tight close framing on faces; tan leather interior, reflective windows; rhythmic engine hum; morning clarity.
  Narrative Function: Transit space for intimate conversation.

### PROP ASSETS
- ID: prop_cigarette
  Name: Cigarette
  Descrip
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_sunlit_ride_smoke",
      "narrative_layer": {
        "narrative_action": "Vincent and Jules ride in a moving vintage car, casually smoking as shifting sunlight and shadows move across their faces.",
        "emotional_beat": "relaxed_flow",
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
      "shot_id": "shot_02_jules_asks_question",
      "narrative_layer": {
        "narrative_action": "Over the engine hum and shifting light, Jules turns to Vincent and asks a question.",
        "emotional_beat": "curious_probe",
        "dialogue": {
          "has_dialogue": true,
          "speaker_asset_id": "char_jules_winnfield",
          "listener_asset_id": "char_vincent_vega",
          "text": null,
          "voice_preset": null
        }
      }
    },
    {
      "shot_id": "shot_03_vincent_voiceover_reply",
      "narrative_layer": {
        "narrative_action": "As the ride continues, Vincent replies in voiceover to Jules’s question.",
        "emotional_beat": "playful_reveal",
        "dialogue": {
          "has_dialogue": true,
          "speaker_asset_id": "char_vincent_vega",
          "listener_asset_id": "char_jules_winnfield",
          "text": "They call it a Royale with Cheese.",
          "voice_preset": null
        }
      }
    }
  ]
}
```
