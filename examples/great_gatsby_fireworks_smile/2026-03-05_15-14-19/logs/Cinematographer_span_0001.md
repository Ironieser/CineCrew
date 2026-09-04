# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 87e46519e37b486c
- **Session ID**: dataset_great_gatsby_fireworks_smile_2026-03-05_15-14-19
- **Timestamp**: 2026-03-05 15:15:53
- **Duration**: 23.03s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3264
- **completion_tokens**: 2284
- **total_tokens**: 5548

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
- **ERA LOCK**: Roaring Twenties (1920s)
- **STYLE OVERRIDES**:
  * color_palette: Warm golds and champagne tones
  * fashion: 1920s formalwear
  * lighting: Fireworks backlight with warm fill

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - ERA LOCK: Roaring Twenties (1920s)
  - COLOR_PALETTE: Warm golds and champagne tones
  - FASHION: 1920s formalwear
  - LIGHTING: Fireworks backlight with warm fill
Plus any shot-specific visual consistency rules.


### NARRATIVE CONTEXT (Read this first to understand the story world)
Time Period: Roaring Twenties, 1920s night
Global Mood: Opulent, nostalgic, enchanting
Key Events: Camera glides past blurred partygoers toward a tuxedoed man., Golden fireworks erupt, bathing the scene in warm light., He turns, revealing a rare, magnetic smile., He raises a crystal coupe in a silent toast., A gentle voiceover: "I'm Gatsby."
Cultural Context: Jazz Age opulence and high-society parties; Art Deco aesthetics; champagne-fueled celebration.

### GLOBAL VISUAL STYLE
Opulent Art Deco glamour; warm golden palette; shallow depth of field; smooth camera glide; exterior night fireworks backlight; romantic nostalgia.

### CHARACTER ASSETS
- ID: char_gatsby
  Name: Gatsby
  Visual: Sharply dressed man in a classic black tuxedo, poised; luminous, magnetic smile under warm fireworks glow.
  Clothing: 1920s formal: black tuxedo with satin lapels, crisp white shirt, black bow tie, polished shoes.
  Personality: Charismatic, enigmatic, self-possessed, gracious; projects warmth with restraint.
  Backstory: Little revealed; known simply as "Gatsby" amid a lavish 1920s party.
  Motivation: To reveal his identity and offer a silent, reassuring toast.

### LOCATION ASSETS
- ID: loc_ext_roaring_twenties_party
  Name: Roaring Twenties Party (Exterior) (EXT)
  Visual: Open-air night under golden fireworks; opulent, champagne-lit ambiance; guests blurred; warm Art Deco glamour.
  Narrative Function: Introduction reveal; place of spectacle and allure.

### PROP ASSETS
- ID: prop_champagne_coupe
  Name: Crystal Champagne Coupe
  Description: Shallow, wide-bowled crystal coupe filled with effervescent champagne, catching warm golden fireworks light during the toast.
- ID: prop_fireworks_display
  N
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_gatsby_silent_toast",
      "staging_layer": {
        "duration_seconds": 6.5,
        "camera": {
          "shot_scale": "MCU",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "Fireworks backlight with warm fill",
        "environment_id": "loc_ext_roaring_twenties_party",
        "entities": [
          {
            "asset_id": "char_gatsby",
            "position": "center_fg",
            "action_state": "turning_to_camera_smiling_raising_coupe"
          },
          {
            "asset_id": "prop_champagne_coupe",
            "position": "center_fg_right",
            "action_state": "held_in_right_hand_raised_for_toast"
          },
          {
            "asset_id": "prop_fireworks_display",
            "position": "background_top_center",
            "action_state": "erupting_bursts"
          }
        ],
        "consistency_constraints": [
          "ERA LOCK: Roaring Twenties (1920s)",
          "COLOR_PALETTE: Warm golds and champagne tones",
          "FASHION: 1920s formalwear",
          "LIGHTING: Fireworks backlight with warm fill",
          "Maintain shallow depth of field — background partygoers remain blurred bokeh",
          "Subtle rack focus to Gatsby during his turn and toast",
          "Camera maintains slight low angle to place fireworks in the sky behind Gatsby",
          "Gatsby remains framed center throughout the shot"
        ]
      }
    }
  ]
}
```
