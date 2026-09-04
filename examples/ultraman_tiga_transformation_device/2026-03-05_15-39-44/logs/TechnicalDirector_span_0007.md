# Agent: TechnicalDirector
- **Span ID**: span_0007
- **Trace ID**: 3117a8ab38794c6e
- **Session ID**: dataset_ultraman_tiga_transformation_device_2026-03-05_15-39-44
- **Timestamp**: 2026-03-05 15:44:43
- **Duration**: 102.76s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 7626
- **completion_tokens**: 8243
- **total_tokens**: 15869

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
- **LOCATION LOCK**: Abstract, indeterminate tech environment with blurred background—non-specific locale (NOT recognizable Earth city, NOT historical site, NOT natural landscape)
- **ERA LOCK**: Unspecified far-future sci-fi era (NOT contemporary or historical)
- **FORBIDDEN ELEMENTS**: Recognizable real-world cities, landmarks, skylines (e.g., Times Square, Eiffel Tower), Historical architecture (cathedrals, temples, pagodas, castles, stone villages), Religious iconography (crosses, halos, altars, stained glass), Angelic or feathered wings (use crystal/mechanical only), Medieval or fantasy elements (swords, armor, runes, magic circles), Steampunk aesthetics (brass gears, Victorian styling), Retro analog tech (CRT monitors, exposed cables, vacu
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_intense_gaze_holds",
      "characters_in_shot": [
        "char_determined_young_man"
      ],
      "character_appearances": {
        "char_determined_young_man": "Young man, red-and-white sci-fi uniform jacket closed, standing centered and squared to camera, jaw set and eyes blazing with resolve"
      },
      "t2i_template": "Cinematic sci-fi close-up at a low, slightly wide angle with shallow depth-of-field; high-key cool white soft fill and gentle bloom. <char_determined_young_man> stands center foreground, shoulders squared, chin subtly lowered toward camera dominance; his right hand hovers near the jacket’s inner seam as if about to slide inside, while his left arm hangs steady at his side. His eyes lock directly through the lens, unwavering. Body language radiates defiant resolve—he occupies the frame decisively with the blurred world receding behind him. Background remains abstract, indeterminate tech forms dissolved into creamy bokeh; no readable text, symbols, or identifiable locale.",
      "i2v_template": "Slow, deliberate dolly-in toward <char_determined_young_man>. He holds the gaze without blinking, a minute breath draws and settles; his brows tighten and his right hand begins to slip along the jacket seam toward the concealed inner pocket in preparation for the draw. Mouth remains tightly closed. No speaking. The blurred abstract background gently breathes with shallow DOF shifts; soft iridescent highlights slide across matte-white surfaces; a faint draft lifts a wisp of hair and eases the jacket fabric. End with his fingers poised at the inner pocket and a subtle upward anticipation in his posture to cleanly cut into the upward-follow of the next shot.",
      "rationale": "A low, front-facing hero CU emphasizes dominance and resolve; micro-prep of the hand seeds the motivation for the draw to device, creating strong continuity into the tilt-up follow."
    },
    {
      "shot_id": "shot_02_draws_device_high",
      "characters_in_shot": [
        "char_determined_young_man"
      ],
      "character_appearances": {
        "char_determined_young_man": "Young man, red-and-white sci-fi uniform jacket slightly opening at the seam, posture braced to draw and raise the device, focused and decisive"
      },
      "t2i_template": "Cinematic sci-fi medium shot at a low angle; cool high-key whites with soft fill and a crisp rim poised to catch the raised object; shallow depth-of-field keeps the background abstract and unreadable. <char_determined_young_man> is centered, torso turned square, eyes already lifted slightly above the lens line, elbow bent and wrist poised at the jacket’s inner seam. The outline of <prop_transformation_device> presses faintly beneath the fabric; his shoulders brace and core tightens, on the verge of pulling and thrusting upward. The blurred environment remains an indeterminate futurist staging space—no signage, no symbols, no location cues.",
      "i2v_template": "Camera tilts up to follow <char_determined_young_man> as his right hand draws <prop_transformation_device> from the jacket in one smooth motion and then thrusts it high overhead. His chest expands and stance firms; the device clears the frame line, catching crisp speculars along white and crystal surfaces as it rises. Mouth remains tightly closed. No speaking. The jacket fabric ripples and settles, rim light skims across knuckles, and the abstract background bokeh drifts softly with the tilt. End with his arm locked out and <prop_transformation_device> held near the top-center of frame, mechanism subtly tensing in anticipation to cut cleanly into the ECU of the device.",
      "rationale": "A low-angle MS plus tilt-up follow elevates the gesture into a heroic beat; the end pose frames the prop ideally for the incoming ECU activation."
    },
    {
      "shot_id": "shot_03_crystal_wings_open",
      "characters_in_shot": [],
      "character_appearances": {},
      "t2i_template": "Hyper-clean ECU at eye level with shallow depth-of-field; crisp white accents kiss the edges of <prop_transformation_device>, specular highlights poised along its crystal surfaces. The device sits centered in the foreground, wings still folded tight and aligned, micro-tolerances showing preloaded tension. The blurred background remains an abstract, non-descript futurist void—no glyphs, no text, no identifiable structures—holding a quiet before the snap.",
      "i2v_template": "Static framing with a precise rack focus across <prop_transformation_device>: focus starts on the central hinge, then snaps to the wing edges as both crystal wings spring outward with a sharp mechanical snap. The opening is symmetrical and clean; micro-vibrations settle quickly as light skims along the facets. Mouth remains tightly closed. No speaking. Ambient motion remains minimal and precise—subtle geometric reflections glide over crystal planes, the shallow DOF breathes after the snap. End with wings fully deployed and a faint, concentrated glow kindling at the core, primed to cut to the face-wash eruption.",
      "rationale": "An ECU isolates the mechanism, fetishizing precision; the rack focus and snap convey a tactile tech beat that sets up the imminent light burst."
    },
    {
      "shot_id": "shot_04_white_light_erupts",
      "characters_in_shot": [
        "char_determined_young_man"
      ],
      "character_appearances": {
        "char_determined_young_man": "Young man, red-and-white sci-fi uniform, face in low-angle close-up; eyes steady, lips pressed, features poised just before being engulfed by intense white light"
      },
      "t2i_template": "Low-angle cinematic close-up with shallow depth-of-field; the frame is prepared for a pure white core eruption with soft cinematic bloom. <char_determined_young_man> fills center foreground, shoulders angled toward camera; his features are tense but calm, eyes fixed forward. At frame right foreground, <prop_transformation_device> is held near his face with wings open; the central crystal glimmers faintly, not yet erupted. The environment is an abstract, blurred, non-descript futurist space; no symbols or readable elements. The moment hangs on the cusp before the light detonates.",
      "i2v_template": "Static camera as the central crystal of <prop_transformation_device> flares—pure white light erupts, surging across <char_determined_young_man>'s face and blowing out exposure. Wrap-around highlights race from frame right to left; he holds his ground, eyelids fluttering once but gaze remaining resolute into the brightness. Mouth remains tightly closed. No speaking. Clean geometric bands of light expand and soften, bloom swells, and the already-blurred background dissolves rapidly toward featureless white. End with only faint silhouette edges of his profile and hand remaining against the wash, ready to cut into total whiteout.",
      "rationale": "Keeping the camera static underscores the power of the eruption; the light’s wrap creates emotional overwhelm and sets a natural bridge into the full white frame."
    },
    {
      "shot_id": "shot_05_frame_swallowed_white",
      "characters_in_shot": [],
      "character_appearances": {},
      "t2i_template": "Extreme close-up framing that is already nearly overexposed; the image is a high-key field with only the faintest residual contours at the extreme edges hinting at former subjects. Lighting is blinding pure white with soft bloom; environment and subjects have dissolved into an abstract, indeterminate void with no readable forms.",
      "i2v_template": "Static camera as the remaining edge detail evaporates—the white field intensifies until the frame becomes a seamless, uniform pure white with no visible contour. Mouth remains tightly closed. No speaking. The bloom breathes once and then steadies; a minimal geometric falloff fades to zero. End by holding on the pristine white frame for a clean cut or dissolve.",
      "rationale": "A total whiteout is the visual culmination of the activation—reducing the frame to pure light provides a definitive, transcendental endpoint."
    }
  ]
}
```
