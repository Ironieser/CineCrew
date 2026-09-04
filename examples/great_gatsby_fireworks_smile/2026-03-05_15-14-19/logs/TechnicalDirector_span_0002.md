# Agent: TechnicalDirector
- **Span ID**: span_0002
- **Trace ID**: 87e46519e37b486c
- **Session ID**: dataset_great_gatsby_fireworks_smile_2026-03-05_15-14-19
- **Timestamp**: 2026-03-05 15:17:02
- **Duration**: 69.26s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 3466
- **completion_tokens**: 4013
- **total_tokens**: 7479

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


#
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_gatsby_silent_toast",
      "characters_in_shot": [
        "char_gatsby"
      ],
      "character_appearances": {
        "char_gatsby": "Adult man, classic 1920s black tuxedo with satin lapels, crisp white shirt, black bow tie, polished shoes; standing upright with back to camera, right hand holding a crystal coupe at waist height; composed, expectant warmth just before turning."
      },
      "t2i_template": "Opulent Art Deco glamour with a warm golden palette; shallow depth of field; MCU at a slight low angle. Lighting: fireworks backlight with warm fill—golden rim from <prop_fireworks_display> outlines shoulders and profile edges while a gentle warm bounce lifts tux textures. <char_gatsby> stands center foreground, back to camera, shoulders squared and relaxed; head subtly cocked as if sensing the lens; right hand loosely holding <prop_champagne_coupe> near his right hip, bowl tilted a touch toward level; left arm at his side. He dominates the frame due to the low angle and central placement; eyeline is implied toward the lens but not yet turned; presence is controlled and inviting. Environment: within <loc_ext_roaring_twenties_party>, the first golden bloom of <prop_fireworks_display> is beginning high top center; the background remains a soft bokeh of revelry and lights, placing him against a haloed night sky.",
      "i2v_template": "Slow dolly-in on a low axis, maintaining center framing; subtle rack focus shifts from the golden bokeh and rim to <char_gatsby>'s turning face. <char_gatsby> inhales almost imperceptibly, shoulders soften; he pivots from back to three-quarter and then to face the lens. His expression warms into a rare, magnetic smile as the golden rim slides across his jawline. He lifts <prop_champagne_coupe> smoothly from waist to eye level, crystal catching and refracting the fireworks glow; he holds it steady in a silent, gracious toast, eyeline locking gently to the viewer. Mouth moves to match speech. Ambient motion: <prop_fireworks_display> blossoms behind in layered golden bursts; drifting embers and faint smoke trail down; champagne bubbles rise and glint in the coupe; a light night breeze stirs tux lapels and hair; distant blurred figures and lights in <loc_ext_roaring_twenties_party> shimmer with subtle sway. Camera eases to a tight MCU, low angle maintained, with <char_gatsby> centered, coupe held at eye line and smile settled, ready for a clean cut.",
      "rationale": "The low-angle MCU with fireworks backlight elevates <char_gatsby>'s reveal into an iconic moment, matching the revelatory warmth beat. The t2i holds the poised, anticipatory instant before he turns and toasts; the i2v executes a smooth, romantic glide-in with a rack focus to accent the turn, smile, and toast, while ambient fireworks and subtle fabric/bubble motion keep the frame alive. Ending centered with the coupe raised provides a natural handoff."
    }
  ]
}
```
