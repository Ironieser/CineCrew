# Agent: TechnicalDirector
- **Span ID**: span_0003
- **Trace ID**: 30c95b42e8c84355
- **Session ID**: dataset_devil_wears_prada_cerulean_sweater_2026-03-05_17-48-05
- **Timestamp**: 2026-03-05 17:50:54
- **Duration**: 61.68s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4135
- **completion_tokens**: 4926
- **total_tokens**: 9061

## Prompt Rendered

```
=== System ===
You are a Storyboard Artist & Prompt Engineer for AI video generation.
You are given a list of shots that already have narrative_layer and staging_layer filled.

Your job: generate the render templates for each shot.

=========================================================
TEMPORAL TWO-PHASE DESIGN (CRITICAL)
=========================================================

t2i_template — THE SETUP (keyframe, T = 0)
  Describe the scene at the SPLIT SECOND BEFORE the main action occurs.
  This is a still image. Show:
  - Where every character is positioned and their posture
  - What they are about to do (but haven't done yet)
  - The emotional atmosphere at that exact moment
  
  ❌ BAD (result state):  "The glass is shattered on the floor."
  ✅ GOOD (setup state): "The glass is tilting off the table edge, liquid starting to spill."
  
  ❌ BAD: "Michael raises his gun."
  ✅ GOOD: "Michael's hand moves toward his jacket, tension in his jaw, Sollozzo watching."

i2v_template — THE EXECUTION (motion, T > 0)
  Describe the movement and consequence that unfolds from that keyframe.
  Structure: [Camera Move] + [Character Actions & Reactions] + [Lip Constraint] + [Ambient Motion]
  
  Include all of:
  1. Camera movement (or "static camera")
  2. Each visible character's action and reaction to others
  3. Lip-sync constraint (MANDATORY — see rules below)
  4. Ambient/environmental motion (never a frozen video)

=========================================================
ASSET PLACEHOLDER RULES
=========================================================
- Use ONLY `<asset_id>` placeholders (e.g. `<char_michael_corleone>`)
- NEVER write character real names, "Picture N", or raw descriptions in the template
- <asset_id> will be replaced with actual appearance descriptions by the assembly pipeline

=========================================================
CHARACTER DATA RULES
=========================================================
characters_in_shot:
  - List the asset_ids of ALL characters VISIBLE in this shot, in order:
    typically left-to-right, foreground-to-background, or by narrative importance
  - Only include characters actually visible (not just heard or implied)
  - Pure environment shots: []

character_appearances:
  - Per-shot description for EACH character in characters_in_shot
  - Must reflect the CHARACTER'S STATE in this specific shot:
    same character in different scenes = different costume/state
  - Format: "Gender/Age, [outfit for this scene], [current physical state/mood]"
  - Example: "Middle-aged man, dark double-breasted suit, sitting rigidly upright"
  - This will be used when assembling the final prompt

=========================================================
LIP-SYNC CONSTRAINT (MANDATORY IN i2v_template)
=========================================================
Every i2v_template MUST include ONE of these exact phrases:
- If narrative_layer.dialogue.has_dialogue = true AND the speaker is visible:
    "Mouth moves to match speech."
- Otherwise (narration / no visible speaker / no dialogue):
    "Mouth remains tightly closed. No speaking."

=========================================================
VISUAL AESTHETICS GUIDE
=========================================================
Match lighting and camera to emotional beat from narrative_layer:

Camera angle (use staging_layer.camera as base, add cinematic reasoning):
  - Power/tension: low angle on dominant character, high angle on submissive
  - Intimacy: eye level, shallow depth of field
  - Isolation: static wide, characters small in frame

Lighting (use staging_layer.lighting, expand to cinematic description):
  - Action/danger: high contrast, rim light
  - Grief/sadness: soft diffused, desaturated
  - Confrontation: hard side light, deep shadows

Motion intensity in i2v:
  - HIGH EMOTION (rage/fear/shock): exaggerated physics, "tears stream", "background speed lines"
  - LOW EMOTION (dialogue/contemplation): micro-movements only — "hair shifts in draft",
    "dust motes dance", "subtle chest rise and fall"
  - IDLE RULE: Never pure static. Always include ambient motion.

=========================================================
RELATIONAL DYNAMICS (when 2+ characters in shot)
=========================================================
t2i_template MUST describe:
  - Who looks at whom (eyelines)
  - Body language contrast (who dominates space)
  - Physical relationship and psychological tension

i2v_template MUST describe:
  - How they react to each other's micro-movements

=========================================================
FORWARD CONTINUITY
=========================================================
End each i2v on a pose/angle that leads naturally into the next shot.
If a "next_shot" context is provided, end so the last frame can cut cleanly.

=========================================================
CRITICAL RULES
=========================================================
1. Output shot_ids MUST exactly match input shot_ids (same order).
2. ALL <asset_id> values MUST come from Asset Context. NEVER invent IDs.
3. t2i_template: describe BEFORE the action (setup state).
4. i2v_template: describe the action HAPPENING (motion + consequence).
5. NEVER put the final assembled prompt — only templates with <asset_id>.



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
The
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_miranda_cold_stare",
      "characters_in_shot": [
        "char_miranda_priestly"
      ],
      "character_appearances": {
        "char_miranda_priestly": "Middle-aged woman, tailored monochrome couture suit with discreet luxury accessories and gold-rimmed glasses, standing poised and dominating, icy contempt fixed offscreen left"
      },
      "t2i_template": "Cold, minimalist editorial close-up; sterile cool high-key lighting with subtle rim from glass reflections outlines <char_miranda_priestly>. Low-angle CU: <char_miranda_priestly> occupies frame_right, torso slightly angled toward offscreen_left, chin lifted a touch, shoulders squared. <prop_gold_rimmed_glasses> rest on the bridge of the nose, catching a narrow cool specular streak. Her pupils are locked offscreen_left toward <char_andrea_sachs>, lips pressed into a thin line. She dominates the frame, the empty space to the left implying the subordinate presence she assesses. Environment hints of <loc_int_fashion_office>: blurred chrome edges and glass partitions, all in cool, desaturated tones with a faint cerulean reflection.",
      "i2v_template": "Camera: slow, deliberate dolly-in at low angle, tightening toward <char_miranda_priestly>'s eyes. As the camera advances, her gaze travels once—subtly scanning up and down across offscreen_left—then returns to settle, a fractional head tilt telegraphing judgment. <prop_gold_rimmed_glasses> catch and release a cold glint as her focus shifts; she draws a restrained breath, jaw tight, shoulders immobile. Mouth remains tightly closed. No speaking. Ambient motion: reflections slide along the glass partition of <loc_int_fashion_office>, a faint draft stirs a few strands of her silver bob, and distant bokeh highlights drift. End with her eyes locking to the height corresponding to the unseen <prop_cerulean_sweater>, holding for a clean cut into the next shot.",
      "rationale": "Low-angle CU and sterile lighting amplify authority and freezing contempt. Framing her frame_right with eyeline offscreen_left establishes the power dynamic and preps the match cut to the sweater."
    },
    {
      "shot_id": "shot_02_sweater_closeup_cerulean",
      "characters_in_shot": [
        "char_andrea_sachs"
      ],
      "character_appearances": {
        "char_andrea_sachs": "Young woman, lumpy cerulean sweater over basic office wear, shoulders slightly hunched and tense, self-conscious under scrutiny"
      },
      "t2i_template": "Cold, minimalist editorial extreme close-up; sterile cool high-key with soft side light reveals knit texture without glare. Eye-level ECU of <prop_cerulean_sweater> worn by <char_andrea_sachs> at center_fg: the pilled, uneven knit fills the frame, the most saturated cerulean element against muted surroundings. <char_andrea_sachs>'s shoulders angle a touch forward, body held still, fingertips poised near the hem just at the edge of focus as if about to fidget. The atmosphere is clinical and dismissive, as if the fabric is under examination. Background collapses into cool, desaturated bokeh of <loc_int_fashion_office> glass and chrome.",
      "i2v_template": "Camera: slow dolly-in at eye level with a gentle rack focus from surface pills to the broader weave of <prop_cerulean_sweater>, preserving cerulean dominance while the background melts deeper into blur. <char_andrea_sachs>'s chest rises and falls shallowly; her shoulders tighten a fraction and a thumb grazes a loose fiber near the hem before stilling in response to the unseen authority. Mouth remains tightly closed. No speaking. Ambient motion: soft reflections from overhead fluorescents drift across the knit, bokeh highlights from <loc_int_fashion_office> glass shift slightly, and the fabric subtly moves with each micro-breath. End by settling focus on a clean patch of knit dead center, holding steady to facilitate a crisp cut back to the observer.",
      "rationale": "ECU isolates the cerulean and texture under a clinical gaze, aligning with dismissive authority while preparing an audio-led transition. Rack focus and micro-movements sustain tension without breaking the sterile aesthetic."
    }
  ]
}
```
