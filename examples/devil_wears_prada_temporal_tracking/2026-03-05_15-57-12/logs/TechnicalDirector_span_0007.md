# Agent: TechnicalDirector
- **Span ID**: span_0007
- **Trace ID**: 2369461831324e3f
- **Session ID**: dataset_devil_wears_prada_temporal_tracking_2026-03-05_15-57-12
- **Timestamp**: 2026-03-05 16:02:27
- **Duration**: 93.41s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 5927
- **completion_tokens**: 5630
- **total_tokens**: 11557

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
- **LOCATION LOCK**: Manhattan, New York City, USA
- **ERA LOCK**: Contemporary (unspecified exact year)
- **STYLE OVERRIDES**:
  * color_palette: sleek monochrome with dark green, white, black accents
  * architecture: dense New York urban streetscape, contemporary signage, yellow cabs

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - LOCATION LOCK: Manhattan, New York City, USA
  - ERA LOCK: Contemporary (unspecified exact year)
  - COLOR_PALETTE: sleek
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_confident_street_strut",
      "characters_in_shot": [
        "char_andy"
      ],
      "character_appearances": {
        "char_andy": "Woman, 20s–30s, dark green double-breasted coat, decisive stride posture with shoulders back and chin level; focused and in control"
      },
      "t2i_template": "Style: High-fashion, glossy urban aesthetic with sleek monochrome palette accented by deep green. Lighting: high-key daylight from overcast sky, soft fill with subtle edge sheen on fabrics. In the split-second before motion, <char_andy> stands mid-step at center frame within <loc_ext_manhattan_street>, front heel hovering just above the pavement, weight coiled to launch forward. <prop_dark_green_double_breasted_coat> hangs with a slight outward flare as if caught mid-sway, structured shoulders sharp. <prop_paper_coffee_cup> is held upright near her torso, perfectly vertical and aligned, fingers relaxed but purposeful. Eyeline fixed straight ahead, projecting command; she dominates the space with squared hips and confident chest, owning the frame. Background reads as dense Manhattan: layered facades, contemporary signage, and a distant <prop_yellow_taxi> shape along the curb; pedestrians and storefronts implied as soft, secondary elements. Emotional atmosphere: poised certainty, the city as her runway—tension held in the stillness before the stride.",
      "i2v_template": "Camera Move: Static gimbal begins a smooth parallel track left-to-right, eye level, keeping <char_andy> centered as the city scrolls behind her. Character Actions & Reactions: <char_andy> drops her poised front heel with a crisp click and launches into a power-walk; shoulders remain square, chin steady. <prop_dark_green_double_breasted_coat> ripples and sways with each step, hemline pulsing outward then settling. <prop_paper_coffee_cup> stays perfectly upright and locked to a consistent position near her torso, not rotating or tilting despite the stride; her hand absorbs micro-shock to maintain alignment. Eyeline remains forward, unflinching, body language radiating control. Lip Constraint: Mouth remains tightly closed. No speaking. Ambient Motion: Reflections slide along shop windows; a distant <prop_yellow_taxi> glides through traffic; pedestrians blur in the far background; a faint steam wisp rises from a street vent; subtle wind lifts a strand of hair and flutters the coat edges. Forward Continuity: End the shot with a <prop_yellow_taxi> beginning to enter the foreground frame from the left, setting up a full occlusion for the next shot while <char_andy> remains centered.",
      "rationale": "We open at eye level to establish intimacy and control, using a clean parallel track to turn the sidewalk into a runway. The upright cup and composed eyeline communicate precision. Ending with a taxi entering frame primes the seamless occlusion transform in Shot 02."
    },
    {
      "shot_id": "shot_02_taxi_occlusion_transform",
      "characters_in_shot": [
        "char_andy"
      ],
      "character_appearances": {
        "char_andy": "Woman, 20s–30s, seamless transition from dark green coat to white tweed with thigh-high Chanel boots during occlusion; stride continuous, self-assured and composed"
      },
      "t2i_template": "Style: Glossy urban fashion-video energy with sleek monochrome palette; white and black accents ready to pop after reveal. Lighting: soft, even daylight with reflective street sheen. At the frozen instant before the occlusion, <char_andy> advances in the midground at center frame within <loc_ext_manhattan_street>, still in <prop_dark_green_double_breasted_coat>, front heel poised to plant, shoulders aligned. <prop_paper_coffee_cup> is upright and anchored near her torso, perfectly vertical. In the foreground, a <prop_yellow_taxi> noses into frame from the left, grill angled to sweep across and cover <char_andy> in a full-frame, left-to-right pass. Eyeline forward; presence unwavering. Spatial tension builds between her controlled center and the impending bold yellow occluder, promising a reveal.",
      "i2v_template": "Camera Move: Maintain smooth gimbal parallel track left-to-right, eye level, matching <char_andy>'s pace while allowing the <prop_yellow_taxi> to overtake foreground. Character Actions & Reactions: As <prop_yellow_taxi> crosses, it fully occludes <char_andy> from view. During the occlusion, her wardrobe transitions seamlessly: <prop_dark_green_double_breasted_coat> swaps to <prop_white_tweed_coat>, and <prop_thigh_high_chanel_boots> become visible as she continues the same rhythmic stride. She re-emerges centered, stride never breaking, chin slightly lifted in triumph; <prop_paper_coffee_cup> remains perfectly upright and in the same relative screen position. Lip Constraint: Mouth remains tightly closed. No speaking. Ambient Motion: Taxi wheels roll with subtle suspension bounce; window reflections smear across its side; background pedestrians and signage slide laterally; faint breeze skims the coat surface and stirs a few strands of hair. Forward Continuity: End as the taxi clears frame to the right with <char_andy> fully revealed in the white tweed look, centered and mid-stride, matching pace and screen position to flow into the next shot.",
      "rationale": "A foreground taxi creates a bold, graphic occlusion for a clean in-camera-feel transformation. The lateral track preserves momentum and continuity, while the cup’s stability sells precision. We end post-reveal with Andy centered to carry speed into Shot 03."
    },
    {
      "shot_id": "shot_03_white_look_stride",
      "characters_in_shot": [
        "char_andy"
      ],
      "character_appearances": {
        "char_andy": "Woman, 20s–30s, white tweed coat with thigh-high Chanel boots, posture tall and assertive; energized momentum, controlled focus"
      },
      "t2i_template": "Style: High-fashion crispness; sleek monochrome palette accenting luminous white. Lighting: overcast soft fill with glossy reflections. At the exact pre-motion beat, <char_andy> stands centered in the foreground within <loc_ext_manhattan_street>, now in <prop_white_tweed_coat> and <prop_thigh_high_chanel_boots>. Her leading heel hovers just above ground, boot angled for the next confident plant; <prop_paper_coffee_cup> remains upright and aligned at her torso, perfectly vertical. Eyeline forward, shoulders squared, stance commanding. The street layers behind her—contemporary signage, rhythmic building lines, hints of yellow cabs further back—compress into a runway-like corridor that she visually dominates.",
      "i2v_template": "Camera Move: Continue smooth parallel gimbal track left-to-right at eye level, matching <char_andy>'s pace and keeping her centered in a medium shot. Character Actions & Reactions: <char_andy> steps down into a renewed, assertive strut; <prop_thigh_high_chanel_boots> land with clean, rhythmic clicks. <prop_white_tweed_coat> responds with crisp fabric flutter and a subtle texture shimmer as it catches the light. <prop_paper_coffee_cup> remains perfectly upright and locked to its screen position, hand absorbing micro-shock to maintain alignment. Her chin stays level, gaze unwavering, shoulders relaxed but strong. Lip Constraint: Mouth remains tightly closed. No speaking. Ambient Motion: Building reflections glide across glass; a blurred yellow cab crosses the far background; street banners shift gently; hair and coat edges stir in a light cross-breeze; faint dust motes and steam waft through shafts of soft daylight. Forward Continuity: End with a slender <prop_narrow_streetlamp> beginning to enter frame from the left foreground, aligning to sweep across <char_andy>'s upper body in the next shot while she stays centered.",
      "rationale": "A tighter medium shot emphasizes texture and luxury details in the white look while preserving runway momentum. The locked cup and steady eyeline reinforce control. We introduce the streetlamp at frame edge to telegraph the next transformation."
    },
    {
      "shot_id": "shot_04_streetlamp_second_transform",
      "characters_in_shot": [
        "char_andy"
      ],
      "character_appearances": {
        "char_andy": "Woman, 20s–30s, transitions from white tweed to sleek black evening jacket as a vertical occluder passes; upper body composed, eyes locked forward"
      },
      "t2i_template": "Style: Polished couture with a kinetic edge; monochrome palette poised to pivot from white to black. Lighting: soft overcast glamour with a slight edge highlight. In the split-second before the occlusion, <char_andy> is centered in the foreground within <loc_ext_manhattan_street>, still in <prop_white_tweed_coat>, shoulders squared and chin poised, front foot about to plant. <prop_paper_coffee_cup> is upright and fixed near her torso. A <prop_narrow_streetlamp> stands just at the left edge of frame, about to sweep across and bisect her upper body as a slim vertical occluder. Eyeline forward; she holds a micro-smile of certainty, dominating the frame while the city recedes.",
      "i2v_template": "Camera Move: Maintain the smooth parallel left-to-right gimbal track, MCU framing, letting the <prop_narrow_streetlamp> drift across the frame. Character Actions & Reactions: As <char_andy> advances, the <prop_narrow_streetlamp> sweeps over her upper body, briefly occluding her torso and shoulders. During this occlusion, her wardrobe transitions seamlessly from <prop_white_tweed_coat> to <prop_black_evening_jacket>. She emerges with the same stride and cadence, chin slightly higher; <prop_paper_coffee_cup> remains perfectly upright and locked in the same screen position. Eyeline stays forward; a subtle boost of confidence registers in her posture. Lip Constraint: Mouth remains tightly closed. No speaking. Ambient Motion: City reflections slide; distant traffic rolls; a hanging banner ripples; hair flickers in a light breeze; the lamp’s shadow briefly grazes her shoulder as it passes. Forward Continuity: As the lamp clears frame, subtly lower the camera by a few inches to prefigure the low-angle push-in of the next shot while keeping <char_andy> centered and moving.",
      "rationale": "A narrow vertical occluder delivers a precise, upper-body match cut for a second transformation. The near-MCU strengthens intimacy and detail, while a subtle camera drop seeds the transition to the power-enhancing low angle in Shot 05."
    },
    {
      "shot_id": "shot_05_black_jacket_finish",
      "characters_in_shot": [
        "char_andy"
      ],
      "character_appearances": {
        "char_andy": "Woman, 20s–30s, sleek black evening jacket with sharp lapels, runway-dominant stride; chin up, unstoppable confidence"
      },
      "t2i_template": "Style: Apex high-fashion authority against a sleek monochrome Manhattan canvas. Lighting: soft daylight with specular edge accents to define structure. In the breath before motion, low-angle MLS frames <char_andy> centered within <loc_ext_manhattan_street>, now in <prop_black_evening_jacket>, weight balanced and ready to drive forward. <prop_paper_coffee_cup> is upright and precisely aligned near her torso, immaculately vertical. Her chin is slightly elevated, shoulders relaxed yet commanding, eyes locked ahead; she fills the frame with dominance while the city towers upward behind her, signage and facades emphasizing vertical power lines.",
      "i2v_template": "Camera Move: Continue the parallel left-to-right gimbal with a subtle push-in from a low angle, maintaining <char_andy> centered. Character Actions & Reactions: <char_andy> powers forward with a runway-precise cadence; the sharp lapels of <prop_black_evening_jacket> catch light on each step. Her posture remains unbroken—chin up, shoulders confident. <prop_paper_coffee_cup> stays perfectly upright and fixed in its relative screen position, steady through micro-impacts. She breathes calmly, gaze unwavering, owning the lane. Lip Con
...
```
