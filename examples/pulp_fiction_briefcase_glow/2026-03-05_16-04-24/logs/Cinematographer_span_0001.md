# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: c3641556678d4269
- **Session ID**: dataset_pulp_fiction_briefcase_glow_2026-03-05_16-04-24
- **Timestamp**: 2026-03-05 16:08:55
- **Duration**: 127.13s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4840
- **completion_tokens**: 9154
- **total_tokens**: 13994

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
- **LOCATION LOCK**: Shadowy interior room (urban apartment or warehouse), modern city, strictly indoors (NOT outdoors, NOT Mediterranean villa, NOT suburban living room)
- **ERA LOCK**: Contemporary modern era (1990s–2020s), timeless urban crime-noir
- **FORBIDDEN ELEMENTS**: Historical period dress (Victorian, 1920s, 1940s fedoras/trench coats), Vintage tech (CRT TVs, rotary phones, typewriters, payphones), Futuristic tech (holograms, AR UI, biometric scanners, LED matrix lighting), Neon cyberpunk color schemes (magenta/teal glow), Bright, high-key or flat lighting; white fluorescent overheads, Exterior views (windows showing daylight, city skyline, palm trees), Outdoor locations (streets, cars, alleys), Religious or supernatural depictions inside the briefcase (angels, demons, skulls, cosmic portals), Text or symbols that explain or reveal the briefcase's contents, Explicit references to specific films or characters (Pulp Fiction, Jules, Vincent Vega, Marcellus Wallace), Mediterranean or European architectural elements, Obvious product logos or brand placements, Smartphones, laptops, modern screens visible in frame, Gunfire or visible firearms, Police sirens or flashing red/blue lights, Comedic tone, slapstick, or camp, Overt teal–orange blockbuster grading
- **STYLE OVERRIDES**:
  * color_palette: Deep blacks and cool desaturated shadows contrasted with an intense warm golden glow
  * lighting_style: Low-key, high-contrast chiaroscuro; single warm source motivated by the briefcase; rapid falloff into darkness
  * architecture: Industrial urban interior (concrete/brick, minimal ornamentation), timeless and contemporary
  * set_design: Sparse, worn, utilitarian room; clutter minimal; no visible windows or windows blacked out
  * props_style: Sleek black hard-shell briefcase with mechanical combination dials (6-6-6); neutral modern furnishings
  * wardrobe: Contemporary dark suit in matte fabrics; no vintage silhouettes or flashy patterns
  * camera_language: Extreme low angle and tight close-ups; slow push-in; shallow depth of field
  * mood_tone: Mysterious, tense, hypnotic crime-noir with visual contrast and suspense
  * vfx_style: Subtle volumetric warm glow from the case; contents never shown; no exaggerated beams or particles beyond gentle haze

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the 
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_vincent_dials_case",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "ECU",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "low-key chiaroscuro pre-glow; cool desaturated shadows with faint warm edge from briefcase seam; rapid falloff into darkness",
        "environment_id": "loc_int_shadowy_room",
        "entities": [
          {
            "asset_id": "prop_black_briefcase",
            "position": "center_fg",
            "action_state": "combination_dials turning to 6-6-6; lid closed"
          },
          {
            "asset_id": "char_vincent",
            "position": "foreground_right",
            "action_state": "leaning_over; right hand turning dials"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Shadowy interior room (urban apartment or warehouse), modern city, strictly indoors (NOT outdoors, NOT Mediterranean villa, NOT suburban living room)",
          "ERA LOCK: Contemporary modern era (1990s–2020s), timeless urban crime-noir",
          "FORBIDDEN: Historical period dress (Victorian, 1920s, 1940s fedoras/trench coats), Vintage tech (CRT TVs, rotary phones, typewriters, payphones), Futuristic tech (holograms, AR UI, biometric scanners, LED matrix lighting), Neon cyberpunk color schemes (magenta/teal glow), Bright, high-key or flat lighting; white fluorescent overheads, Exterior views (windows showing daylight, city skyline, palm trees), Outdoor locations (streets, cars, alleys), Religious or supernatural depictions inside the briefcase (angels, demons, skulls, cosmic portals), Text or symbols that explain or reveal the briefcase's contents, Explicit references to specific films or characters (Pulp Fiction, Jules, Vincent Vega, Marcellus Wallace), Mediterranean or European architectural elements, Obvious product logos or brand placements, Smartphones, laptops, modern screens visible in frame, Gunfire or visible firearms, Police sirens or flashing red/blue lights, Comedic tone, slapstick, or camp, Overt teal–orange blockbuster grading",
          "COLOR_PALETTE: Deep blacks and cool desaturated shadows contrasted with an intense warm golden glow",
          "LIGHTING_STYLE: Low-key, high-contrast chiaroscuro; single warm source motivated by the briefcase; rapid falloff into darkness",
          "ARCHITECTURE: Industrial urban interior (concrete/brick, minimal ornamentation), timeless and contemporary",
          "SET_DESIGN: Sparse, worn, utilitarian room; clutter minimal; no visible windows or windows blacked out",
          "PROPS_STYLE: Sleek black hard-shell briefcase with mechanical combination dials (6-6-6); neutral modern furnishings",
          "WARDROBE: Contemporary dark suit in matte fabrics; no vintage silhouettes or flashy patterns",
          "CAMERA_LANGUAGE: Extreme low angle and tight close-ups; slow push-in; shallow depth of field",
          "MOOD_TONE: Mysterious, tense, hypnotic crime-noir with visual contrast and suspense",
          "VFX_STYLE: Subtle volumetric warm glow from the case; contents never shown; no exaggerated beams or particles beyond gentle haze",
          "Shot-specific: Combination dials must clearly read 6-6-6 at the end of the turn",
          "Shot-specific: Briefcase remains closed; only a hairline warm edge leak permitted",
          "Shot-specific: Vincent’s cigarette remains unlit (if visible)"
        ]
      }
    },
    {
      "shot_id": "shot_02_latches_pop_open",
      "staging_layer": {
        "duration_seconds": 2.2,
        "camera": {
          "shot_scale": "CU",
          "angle": "low",
          "movement": "rack_focus + slight_tilt_up"
        },
        "lighting": "low-key chiaroscuro; first warm spill emerges as lid lifts; deep cool shadows elsewhere",
        "environment_id": "loc_int_shadowy_room",
        "entities": [
          {
            "asset_id": "prop_black_briefcase",
            "position": "center_fg",
            "action_state": "latches releasing; lid beginning to rise"
          },
          {
            "asset_id": "char_vincent",
            "position": "foreground_right",
            "action_state": "hand lifting lid"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Shadowy interior room (urban apartment or warehouse), modern city, strictly indoors (NOT outdoors, NOT Mediterranean villa, NOT suburban living room)",
          "ERA LOCK: Contemporary modern era (1990s–2020s), timeless urban crime-noir",
          "FORBIDDEN: Historical period dress (Victorian, 1920s, 1940s fedoras/trench coats), Vintage tech (CRT TVs, rotary phones, typewriters, payphones), Futuristic tech (holograms, AR UI, biometric scanners, LED matrix lighting), Neon cyberpunk color schemes (magenta/teal glow), Bright, high-key or flat lighting; white fluorescent overheads, Exterior views (windows showing daylight, city skyline, palm trees), Outdoor locations (streets, cars, alleys), Religious or supernatural depictions inside the briefcase (angels, demons, skulls, cosmic portals), Text or symbols that explain or reveal the briefcase's contents, Explicit references to specific films or characters (Pulp Fiction, Jules, Vincent Vega, Marcellus Wallace), Mediterranean or European architectural elements, Obvious product logos or brand placements, Smartphones, laptops, modern screens visible in frame, Gunfire or visible firearms, Police sirens or flashing red/blue lights, Comedic tone, slapstick, or camp, Overt teal–orange blockbuster grading",
          "COLOR_PALETTE: Deep blacks and cool desaturated shadows contrasted with an intense warm golden glow",
          "LIGHTING_STYLE: Low-key, high-contrast chiaroscuro; single warm source motivated by the briefcase; rapid falloff into darkness",
          "ARCHITECTURE: Industrial urban interior (concrete/brick, minimal ornamentation), timeless and contemporary",
          "SET_DESIGN: Sparse, worn, utilitarian room; clutter minimal; no visible windows or windows blacked out",
          "PROPS_STYLE: Sleek black hard-shell briefcase with mechanical combination dials (6-6-6); neutral modern furnishings",
          "WARDROBE: Contemporary dark suit in matte fabrics; no vintage silhouettes or flashy patterns",
          "CAMERA_LANGUAGE: Extreme low angle and tight close-ups; slow push-in; shallow depth of field",
          "MOOD_TONE: Mysterious, tense, hypnotic crime-noir with visual contrast and suspense",
          "VFX_STYLE: Subtle volumetric warm glow from the case; contents never shown; no exaggerated beams or particles beyond gentle haze",
          "Shot-specific: Emphasize the latch release moment; contents must remain unseen as lid begins to rise",
          "Shot-specific: Initial warm spill should flare subtly; no visible interior details",
          "Shot-specific: Vincent’s cigarette remains unlit (if visible)"
        ]
      }
    },
    {
      "shot_id": "shot_03_golden_light_spills",
      "staging_layer": {
        "duration_seconds": 3.2,
        "camera": {
          "shot_scale": "MLS",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "low-key chiaroscuro with intense warm spill from the briefcase; subtle haze for gentle volumetrics; rapid falloff to deep blacks",
        "environment_id": "loc_int_shadowy_room",
        "entities": [
          {
            "asset_id": "prop_black_briefcase",
            "position": "foreground_center",
            "action_state": "open; pouring warm light"
          },
          {
            "asset_id": "char_vincent",
            "position": "center_midground",
            "action_state": "leaning_over; staring into light"
          },
          {
            "asset_id": "prop_unlit_cigarette",
            "position": "near_vincent_face",
            "action_state": "clenched between lips; unlit"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Shadowy interior room (urban apartment or warehouse), modern city, strictly indoors (NOT outdoors, NOT Mediterranean villa, NOT suburban living room)",
          "ERA LOCK: Contemporary modern era (1990s–2020s), timeless urban crime-noir",
          "FORBIDDEN: Historical period dress (Victorian, 1920s, 1940s fedoras/trench coats), Vintage tech (CRT TVs, rotary phones, typewriters, payphones), Futuristic tech (holograms, AR UI, biometric scanners, LED matrix lighting), Neon cyberpunk color schemes (magenta/teal glow), Bright, high-key or flat lighting; white fluorescent overheads, Exterior views (windows showing daylight, city skyline, palm trees), Outdoor locations (streets, cars, alleys), Religious or supernatural depictions inside the briefcase (angels, demons, skulls, cosmic portals), Text or symbols that explain or reveal the briefcase's contents, Explicit references to specific films or characters (Pulp Fiction, Jules, Vincent Vega, Marcellus Wallace), Mediterranean or European architectural elements, Obvious product logos or brand placements, Smartphones, laptops, modern screens visible in frame, Gunfire or visible firearms, Police sirens or flashing red/blue lights, Comedic tone, slapstick, or camp, Overt teal–orange blockbuster grading",
          "COLOR_PALETTE: Deep blacks and cool desaturated shadows contrasted with an intense warm golden glow",
          "LIGHTING_STYLE: Low-key, high-contrast chiaroscuro; single warm source motivated by the briefcase; rapid falloff into darkness",
          "ARCHITECTURE: Industrial urban interior (concrete/brick, minimal ornamentation), timeless and contemporary",
          "SET_DESIGN: Sparse, worn, utilitarian room; clutter minimal; no visible windows or windows blacked out",
          "PROPS_STYLE: Sleek black hard-shell briefcase with mechanical combination dials (6-6-6); neutral modern furnishings",
          "WARDROBE: Contemporary dark suit in matte fabrics; no vintage silhouettes or flashy patterns",
          "CAMERA_LANGUAGE: Extreme low angle and tight close-ups; slow push-in; shallow depth of field",
          "MOOD_TONE: Mysterious, tense, hypnotic crime-noir with visual contrast and suspense",
          "VFX_STYLE: Subtle volumetric warm glow from the case; contents never shown; no exaggerated beams or particles beyond gentle haze",
          "Shot-specific: No interior contents visible; camera must never cross the plane of the case opening",
          "Shot-specific: Maintain windowless feel; glow should illuminate only immediate surroundings",
          "Shot-specific: Haze only to the extent of gentle volumetrics; no floating particles or beams"
        ]
      }
    },
    {
      "shot_id": "shot_04_vincent_bathed_meson",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "POV",
          "angle": "low",
          "movement": "slow_dolly_in"
        },
        "lighting": "low-key chiaroscuro; strong warm glow on Vincent’s face; background collapses to near-black",
        "environment_id": "loc_int_shadowy_room",
        "entities": [
          {
            "asset_id": "char_vincent",
            "position": "center_fg",
            "action_state": "mesmerized stare into the briefcase"
          },
          {
            "asset_id": "prop_unlit_cigarette",
            "position": "near_vincent_face",
            "action_state": "between lips; unlit"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: Shadowy interior room (urban apartment or warehouse), modern city, strictly indoors (NOT outdoors, NOT Mediterranean villa, NOT suburban living room)",
          "ERA LOCK: Contemporary modern era (1990s–2020s), timeless urban crime-noir",
          "FORBIDDEN: Historical period dress (Victorian, 1920s, 1940s fedoras/trench coats), Vintage tech (CRT TVs, rotary phones, typewriters, payphones), Futuristi
...
```
