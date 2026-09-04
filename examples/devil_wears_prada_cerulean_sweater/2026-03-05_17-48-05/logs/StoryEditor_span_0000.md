# Agent: StoryEditor
- **Span ID**: span_0000
- **Trace ID**: 30c95b42e8c84355
- **Session ID**: dataset_devil_wears_prada_cerulean_sweater_2026-03-05_17-48-05
- **Timestamp**: 2026-03-05 17:48:59
- **Duration**: 23.93s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 2871
- **completion_tokens**: 3319
- **total_tokens**: 6190

## Input (preview)

```
Inside a pristine, cold-toned, high-end fashion office, Miranda Priestly, an intimidating female editor with silver hair and gold-rimmed glasses, stares down with absolute, piercing contempt. The camera cuts back and forth between Miranda's cold, calculating micro-expressions and a tight, highly detailed close-up of the nervous young assistant Andrea "Andy" Sachs's lumpy, textured, cerulean blue sweater. Miranda slowly looks Andy up and down, her gaze alone stripping away any remaining confidenc...
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
  Backstory: Powerful fashion editor known for uncompromising standards; commands the room with silent dominance.
  Motivation: Undercut Andy’s confidence and assert taste authority by dissecting her sweater’s color.
- ID: char_andrea_sachs
  Name: Andrea "Andy" Sachs
  Visual: Nervous young assistant; anxious posture; lumpy, textured cerulean blue sweater; overwhelmed by Miranda’s piercing gaze.
  Clothing: Lumpy cerulean sweater over basic office wear; practical, understated.
  Personality: Earnest, inexperienced, insecure; eager to learn, vulnerable to criticism.
  Backstory: New to high-fashion editorial environment; lacks industry fluency; striving to fit in.
  Motivation: Survive Miranda’s critique, retain dignity, and seek approval.

### LOCATION ASSETS
- ID: loc_int_fashion_office
  Name: High-End Fashion Office (INT)
  Visual: Pristine, cold-toned, minimalist; glass and chrome surfaces; crisp, sterile lighting; executive desk and designer details; freezing atmosphere.
  Narrative Function: Plac
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_miranda_cold_stare",
      "narrative_layer": {
        "narrative_action": "Miranda silently looks Andy up and down with piercing contempt.",
        "emotional_beat": "freezing_contempt",
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
      "shot_id": "shot_02_sweater_closeup_cerulean",
      "narrative_layer": {
        "narrative_action": "Andy’s lumpy cerulean sweater is shown as Miranda speaks in voiceover.",
        "emotional_beat": "dismissive_authority",
        "dialogue": {
          "has_dialogue": true,
          "speaker_asset_id": "char_miranda_priestly",
          "listener_asset_id": "char_andrea_sachs",
          "text": "That sweater is not just blue. It's actually cerulean.",
          "voice_preset": null
        }
      }
    }
  ]
}
```
