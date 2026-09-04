# Agent: Cinematographer
- **Span ID**: span_0001
- **Trace ID**: 67e756dc35904d4c
- **Session ID**: dataset_BetterCallSaul2_2026-03-05_07-58-36
- **Timestamp**: 2026-03-05 08:02:12
- **Duration**: 62.34s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4581
- **completion_tokens**: 5138
- **total_tokens**: 9719

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
- **LOCATION LOCK**: United States courtroom interior (trial-level) — NOT UK/European courts; NOT exterior locations
- **ERA LOCK**: Contemporary (2010s–present) United States with legacy AV equipment (CRT television on rolling AV cart)
- **FORBIDDEN ELEMENTS**: British barrister wigs or white powdered wigs, UK royal crest, British courtroom signage, or Union Jack in courtroom, European-style enclosed defendant dock or green leather benches, Flat-panel TV, projector, smartboard, or holographic/futuristic displays used to show the evidence video, Smartphones or tablets used as the primary display for the evidence video, News cameras or TV crews inside the courtroom, Audience applause, laugh track, or comedic sound effects, Gallery outbursts or audible jury reactions (maintain dead-silent courtroom), Graphic violence or depiction of real persons being harmed in the surveillance video, Excessive gavel use or comedic gavel banging, Non-American judicial wardrobe (ornate colored robes) or military-style uniforms for the judge, Exterior establishing shots or non-courtroom architectural elements within the scene
- **STYLE OVERRIDES**:
  * legal_system: United States adversarial trial courtroom with strict decorum
  * courtroom_technology: Aging CRT television on rolling AV cart with wired VCR/DVD player; audio via cart speakers
  * architecture: Wood-paneled American courtroom interior with judge's bench, counsel tables, gallery seating; simple fluorescent lighting
  * wardrobe: Judge in plain black robe (no wig); attorneys in contemporary business suits; Saul wears a cheap tie
  * props: CRT TV on AV cart; remote or wired controls; physical evidence binders; tabletop microphones at counsel tables
  * color_palette: Muted neutrals and warm varnished wood with cool fluorescent whites; avoid neon or glossy cinematic color
  * tone: Tense, awkward, darkly comedic; dead-silent courtroom during the judge's reaction
  * sound_design: Natural room tone only; no music stings; no laugh track
  * evidence_display: The surveillance video must be played on the CRT television and appear low-resolution and slightly blurry

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: United States courtroom interior (tria
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_saul_pleads_leniency",
      "staging_layer": {
        "duration_seconds": 4.0,
        "camera": {
          "shot_scale": "MS",
          "angle": "eye_level",
          "movement": "slow_dolly_in"
        },
        "lighting": "simple fluorescent overhead, soft fill",
        "environment_id": "loc_int_courtroom",
        "entities": [
          {
            "asset_id": "char_saul",
            "position": "center_fg",
            "action_state": "waving_arms_pleading_toward_bench"
          },
          {
            "asset_id": "prop_judges_bench",
            "position": "background_center",
            "action_state": "static"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: United States courtroom interior (trial-level) — NOT UK/European courts; NOT exterior locations",
          "ERA LOCK: Contemporary (2010s–present) United States with legacy AV equipment (CRT television on rolling AV cart)",
          "FORBIDDEN: British barrister wigs or white powdered wigs, UK royal crest, British courtroom signage, or Union Jack in courtroom, European-style enclosed defendant dock or green leather benches, Flat-panel TV, projector, smartboard, or holographic/futuristic displays used to show the evidence video, Smartphones or tablets used as the primary display for the evidence video, News cameras or TV crews inside the courtroom, Audience applause, laugh track, or comedic sound effects, Gallery outbursts or audible jury reactions (maintain dead-silent courtroom), Graphic violence or depiction of real persons being harmed in the surveillance video, Excessive gavel use or comedic gavel banging, Non-American judicial wardrobe (ornate colored robes) or military-style uniforms for the judge, Exterior establishing shots or non-courtroom architectural elements within the scene",
          "LEGAL_SYSTEM: United States adversarial trial courtroom with strict decorum",
          "COURTROOM_TECHNOLOGY: Aging CRT television on rolling AV cart with wired VCR/DVD player; audio via cart speakers",
          "ARCHITECTURE: Wood-paneled American courtroom interior with judge's bench, counsel tables, gallery seating; simple fluorescent lighting",
          "WARDROBE: Judge in plain black robe (no wig); attorneys in contemporary business suits; Saul wears a cheap tie",
          "PROPS: CRT TV on AV cart; remote or wired controls; physical evidence binders; tabletop microphones at counsel tables",
          "COLOR_PALETTE: Muted neutrals and warm varnished wood with cool fluorescent whites; avoid neon or glossy cinematic color",
          "TONE: Tense, awkward, darkly comedic; dead-silent courtroom during the judge's reaction",
          "SOUND_DESIGN: Natural room tone only; no music stings; no laugh track",
          "EVIDENCE_DISPLAY: The surveillance video must be played on the CRT television and appear low-resolution and slightly blurry",
          "Shot-specific: Saul’s wide, cheap tie must be visibly askew; Judge remains off-camera in this shot"
        ]
      }
    },
    {
      "shot_id": "shot_02_tv_video_plays",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "MLS",
          "angle": "eye_level",
          "movement": "rack_focus"
        },
        "lighting": "simple fluorescent overhead, soft fill",
        "environment_id": "loc_int_courtroom",
        "entities": [
          {
            "asset_id": "char_saul",
            "position": "frame_left",
            "action_state": "arm_extended_pointing_toward_tv"
          },
          {
            "asset_id": "prop_rolling_cart",
            "position": "frame_right",
            "action_state": "stationary"
          },
          {
            "asset_id": "prop_crt_television",
            "position": "frame_right",
            "action_state": "screen_flickering_playback"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: United States courtroom interior (trial-level) — NOT UK/European courts; NOT exterior locations",
          "ERA LOCK: Contemporary (2010s–present) United States with legacy AV equipment (CRT television on rolling AV cart)",
          "FORBIDDEN: British barrister wigs or white powdered wigs, UK royal crest, British courtroom signage, or Union Jack in courtroom, European-style enclosed defendant dock or green leather benches, Flat-panel TV, projector, smartboard, or holographic/futuristic displays used to show the evidence video, Smartphones or tablets used as the primary display for the evidence video, News cameras or TV crews inside the courtroom, Audience applause, laugh track, or comedic sound effects, Gallery outbursts or audible jury reactions (maintain dead-silent courtroom), Graphic violence or depiction of real persons being harmed in the surveillance video, Excessive gavel use or comedic gavel banging, Non-American judicial wardrobe (ornate colored robes) or military-style uniforms for the judge, Exterior establishing shots or non-courtroom architectural elements within the scene",
          "LEGAL_SYSTEM: United States adversarial trial courtroom with strict decorum",
          "COURTROOM_TECHNOLOGY: Aging CRT television on rolling AV cart with wired VCR/DVD player; audio via cart speakers",
          "ARCHITECTURE: Wood-paneled American courtroom interior with judge's bench, counsel tables, gallery seating; simple fluorescent lighting",
          "WARDROBE: Judge in plain black robe (no wig); attorneys in contemporary business suits; Saul wears a cheap tie",
          "PROPS: CRT TV on AV cart; remote or wired controls; physical evidence binders; tabletop microphones at counsel tables",
          "COLOR_PALETTE: Muted neutrals and warm varnished wood with cool fluorescent whites; avoid neon or glossy cinematic color",
          "TONE: Tense, awkward, darkly comedic; dead-silent courtroom during the judge's reaction",
          "SOUND_DESIGN: Natural room tone only; no music stings; no laugh track",
          "EVIDENCE_DISPLAY: The surveillance video must be played on the CRT television and appear low-resolution and slightly blurry",
          "Shot-specific: Keep Saul frame-left and CRT on frame-right; rack focus from Saul’s pointing hand to the flickering CRT screen; on-screen content remains indistinct and non-graphic"
        ]
      }
    },
    {
      "shot_id": "shot_03_judge_disgust_reaction",
      "staging_layer": {
        "duration_seconds": 3.0,
        "camera": {
          "shot_scale": "CU",
          "angle": "low",
          "movement": "static"
        },
        "lighting": "simple fluorescent overhead, minimal fill",
        "environment_id": "loc_int_courtroom",
        "entities": [
          {
            "asset_id": "char_judge",
            "position": "center_fg",
            "action_state": "staring_down_unamused"
          },
          {
            "asset_id": "prop_judges_bench",
            "position": "background_center",
            "action_state": "static"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: United States courtroom interior (trial-level) — NOT UK/European courts; NOT exterior locations",
          "ERA LOCK: Contemporary (2010s–present) United States with legacy AV equipment (CRT television on rolling AV cart)",
          "FORBIDDEN: British barrister wigs or white powdered wigs, UK royal crest, British courtroom signage, or Union Jack in courtroom, European-style enclosed defendant dock or green leather benches, Flat-panel TV, projector, smartboard, or holographic/futuristic displays used to show the evidence video, Smartphones or tablets used as the primary display for the evidence video, News cameras or TV crews inside the courtroom, Audience applause, laugh track, or comedic sound effects, Gallery outbursts or audible jury reactions (maintain dead-silent courtroom), Graphic violence or depiction of real persons being harmed in the surveillance video, Excessive gavel use or comedic gavel banging, Non-American judicial wardrobe (ornate colored robes) or military-style uniforms for the judge, Exterior establishing shots or non-courtroom architectural elements within the scene",
          "LEGAL_SYSTEM: United States adversarial trial courtroom with strict decorum",
          "COURTROOM_TECHNOLOGY: Aging CRT television on rolling AV cart with wired VCR/DVD player; audio via cart speakers",
          "ARCHITECTURE: Wood-paneled American courtroom interior with judge's bench, counsel tables, gallery seating; simple fluorescent lighting",
          "WARDROBE: Judge in plain black robe (no wig); attorneys in contemporary business suits; Saul wears a cheap tie",
          "PROPS: CRT TV on AV cart; remote or wired controls; physical evidence binders; tabletop microphones at counsel tables",
          "COLOR_PALETTE: Muted neutrals and warm varnished wood with cool fluorescent whites; avoid neon or glossy cinematic color",
          "TONE: Tense, awkward, darkly comedic; dead-silent courtroom during the judge's reaction",
          "SOUND_DESIGN: Natural room tone only; no music stings; no laugh track",
          "EVIDENCE_DISPLAY: The surveillance video must be played on the CRT television and appear low-resolution and slightly blurry",
          "Shot-specific: Judge framed alone in CU from slightly low angle to emphasize authority; no crowd reactions visible or audible"
        ]
      }
    },
    {
      "shot_id": "shot_04_saul_deflates_tie",
      "staging_layer": {
        "duration_seconds": 3.5,
        "camera": {
          "shot_scale": "MCU",
          "angle": "eye_level",
          "movement": "slow_dolly_in"
        },
        "lighting": "simple fluorescent overhead, soft fill",
        "environment_id": "loc_int_courtroom",
        "entities": [
          {
            "asset_id": "char_saul",
            "position": "center_fg",
            "action_state": "lowering_arm_then_adjusting_tie_avoiding_eye_contact"
          }
        ],
        "consistency_constraints": [
          "LOCATION LOCK: United States courtroom interior (trial-level) — NOT UK/European courts; NOT exterior locations",
          "ERA LOCK: Contemporary (2010s–present) United States with legacy AV equipment (CRT television on rolling AV cart)",
          "FORBIDDEN: British barrister wigs or white powdered wigs, UK royal crest, British courtroom signage, or Union Jack in courtroom, European-style enclosed defendant dock or green leather benches, Flat-panel TV, projector, smartboard, or holographic/futuristic displays used to show the evidence video, Smartphones or tablets used as the primary display for the evidence video, News cameras or TV crews inside the courtroom, Audience applause, laugh track, or comedic sound effects, Gallery outbursts or audible jury reactions (maintain dead-silent courtroom), Graphic violence or depiction of real persons being harmed in the surveillance video, Excessive gavel use or comedic gavel banging, Non-American judicial wardrobe (ornate colored robes) or military-style uniforms for the judge, Exterior establishing shots or non-courtroom architectural elements within the scene",
          "LEGAL_SYSTEM: United States adversarial trial courtroom with strict decorum",
          "COURTROOM_TECHNOLOGY: Aging CRT television on rolling AV cart with wired VCR/DVD player; audio via cart speakers",
          "ARCHITECTURE: Wood-paneled American courtroom interior with judge's bench, counsel tables, gallery seating; simple fluorescent lighting",
          "WARDROBE: Judge in plain black robe (no wig); attorneys in contemporary business suits; Saul wears a cheap tie",
          "PROPS: CRT TV on AV cart; remote or wired controls; physical evidence binders; tabletop microphones at counsel tables",
          "COLOR_PALETTE: Muted neutrals and warm varnished wood with cool fluorescent whites; avoid neon or glossy cinematic color",
   
...
```
