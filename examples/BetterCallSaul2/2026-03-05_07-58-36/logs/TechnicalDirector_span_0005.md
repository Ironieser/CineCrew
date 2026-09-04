# Agent: TechnicalDirector
- **Span ID**: span_0005
- **Trace ID**: 67e756dc35904d4c
- **Session ID**: dataset_BetterCallSaul2_2026-03-05_07-58-36
- **Timestamp**: 2026-03-05 08:04:02
- **Duration**: 89.99s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 7002
- **completion_tokens**: 6814
- **total_tokens**: 13816

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
- **LOCATION LOCK**: United States courtroom interior (trial-level) — NOT UK/European courts; NOT exterior locations
- **ERA LOCK**: Contemporary (2010s–present) United States with legacy AV equipment (CRT television on rolling AV cart)
- **FORBIDDEN ELEMENTS**: British barrister wigs or white powdered wigs, UK royal crest, British courtroom signage, or Union Jack in courtroom, European-style enclosed defendant dock or green leather benches, Flat-panel TV, projector, smartboard, or holographic/futuristic displays used to show the evidence video, Smartphones or tablets used as the primary display for the evidence video, News cameras or TV crews inside the courtroom, Audience applause, laugh track, or comedic sound effects, Gallery outbursts or au
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_saul_pleads_leniency",
      "characters_in_shot": [
        "char_saul"
      ],
      "character_appearances": {
        "char_saul": "Man in his 30s–40s, cheap oversized suit with a wide patterned tie visibly askew, flushed and sweating, posture taut and poised mid-plea"
      },
      "t2i_template": "Style: Grounded, realistic, muted neutrals and warm wood tones within <loc_int_courtroom>. Lighting: simple fluorescent overhead with soft fill, gentle sheen on varnished wood. <char_saul> stands center foreground facing <prop_judges_bench> at background center; shoulders squared, elbows lifted, open hands hovered at chest height just before beginning to gesture. Eyeline: <char_saul> looks upward past camera line toward the elevated position of <char_judge> (off-frame), signaling the power imbalance. Body language contrast: <char_saul> leans forward into the space, trying to command attention; the massive <prop_judges_bench> looms behind, emphasizing authority over him. Environment: Wood-paneled American courtroom, tabletop microphones and binders implied at counsel tables, cool fluorescent whites; no audience movement visible.",
      "i2v_template": "Camera Move: Slow dolly in at eye level, framing tightens from MS toward Saul’s upper torso and hands. Character Actions & Reactions: <char_saul> launches into open-palmed gestures toward <prop_judges_bench>, shoulders rising and falling with emphasis; he glances up at the unseen <char_judge> as if seeking approval, then back to center, intensifying his plea. Mouth moves to match speech. Ambient Motion: Tie end flutters slightly with each gesture; sweat glints and gathers at his temple; dust motes drift in the overhead light; subtle fluorescent flicker plays across the wood. The move settles with his near hand starting to extend toward frame-right, setting up the cut to his pointing in the next shot.",
      "rationale": "Eye-level MS with slow dolly-in keeps us intimate with Saul’s performance while the looming bench underscores the power imbalance. The setup hands hovering before motion emphasizes the split second before his theatrical gestures begin, matching the pleading_insistence beat."
    },
    {
      "shot_id": "shot_02_tv_video_plays",
      "characters_in_shot": [
        "char_saul"
      ],
      "character_appearances": {
        "char_saul": "Man in his 30s–40s, cheap oversized suit, wide tie still askew, arm extended in a confident showman’s point toward the TV, nervous energy beneath the bravado"
      },
      "t2i_template": "Style: Grounded realism with muted palette inside <loc_int_courtroom>. Lighting: simple fluorescent overhead, soft fill. Framing at MLS: <char_saul> stands frame-left in profile toward frame-right, arm extended with index finger aimed toward <prop_crt_television> resting on <prop_rolling_cart> at frame-right. The CRT screen is dark with a faint standby glow, cart cables slack along the shelf. Eyeline: <char_saul> splits his glance—chin tipped toward the off-frame <char_judge> while pointing, trying to direct attention to the TV. Dominance: <char_saul> reaches across the space, but the inert, boxy CRT claims visual gravity. Environment: Wood-paneled walls, counsel tables soft in the background; quiet, orderly courtroom.",
      "i2v_template": "Camera Move: Begin focused on <char_saul>’s extended hand at frame-left, then perform a smooth rack focus to <prop_crt_television> at frame-right as the screen comes to life. Character Actions & Reactions: <char_saul> holds the point with a flourish, shoulders squared; as the screen activates, his posture lifts with forced confidence and then tenses slightly as the image proves indistinct. Mouth remains tightly closed. No speaking. Ambient Motion: The CRT screen flickers to a low-resolution, slightly blurry feed; scanlines roll subtly; a small static shimmer crawls along the edges; the <prop_rolling_cart> vibrates faintly as the TV activates; coiled cables sway a touch. On-screen content stays vague: shadowy, non-graphic silhouettes and a jittery timestamp remain unreadable. Hold on the glowing CRT to set up a cut to the Judge’s reaction.",
      "rationale": "The rack focus shifts attention from Saul’s theatricality to the evidence monitor, building rising tension. The indistinct, low-res CRT image preserves tone and constraints while motivating the judge’s reaction."
    },
    {
      "shot_id": "shot_03_judge_disgust_reaction",
      "characters_in_shot": [
        "char_judge"
      ],
      "character_appearances": {
        "char_judge": "Elderly man, plain black judicial robe, silver hair, composed posture behind the bench, eyes narrowed in unamused disgust"
      },
      "t2i_template": "Style: Realistic, austere close-up from a slightly low angle within <loc_int_courtroom>. Lighting: overhead fluorescent with minimal fill, casting sober shadows into the eye sockets. <char_judge> fills center foreground behind the edge of <prop_judges_bench>; chin slightly lowered, eyes fixed downward toward where <char_saul> would stand. Eyeline and power: <char_judge> looks down past the lens, dominating the frame; no other faces intrude. Environment: Wood-paneled backdrop, American bench detailing; quiet, grave decorum with no visible gallery reaction.",
      "i2v_template": "Camera Move: Static CU from a low angle, unflinching. Character Actions & Reactions: <char_judge> tightens his stare, eyelids narrowing incrementally; a controlled exhale lifts and lowers his chest; the head tilts by a few degrees as his expression settles into cold disapproval, gaze unwavering toward the floor of the court. Mouth remains tightly closed. No speaking. Ambient Motion: Subtle fluorescent flicker rolls across the bench’s varnished edge; a faint shimmer of dust moves through the light; robe fabric breathes slightly with his posture. Hold the locked stare downward to flow into the cut back to Saul’s embarrassment.",
      "rationale": "A static low-angle CU isolates authority and disapproval, heightening the awkward silence and setting up Saul’s deflated response."
    },
    {
      "shot_id": "shot_04_saul_deflates_tie",
      "characters_in_shot": [
        "char_saul"
      ],
      "character_appearances": {
        "char_saul": "Man in his 30s–40s, cheap oversized suit, wide patterned tie still askew, flushed and sweaty, shoulders slumping as embarrassment takes hold"
      },
      "t2i_template": "Style: Intimate, grounded realism in <loc_int_courtroom>; muted colors. Lighting: simple fluorescent overhead with soft fill easing shadows. <char_saul> stands center foreground; one arm still slightly raised from the point, fingers hovering near his chest; the other hand hangs, not yet lifting. Eyeline: his gaze drops away from the elevated <char_judge> (off-frame), chin tucking toward his collarbone. Power dynamic: <char_saul> shrinks within the frame, space around him feels larger. Environment: Warm wood textures and cool fluorescent highlights; courtroom remains orderly and still.",
      "i2v_template": "Camera Move: Slow, gentle dolly in from MCU toward a tighter framing on torso and face. Character Actions & Reactions: <char_saul> freezes, then his extended arm sinks to his side; he inhales shallowly and reaches up with shaky fingers to fuss at the knot of his wide tie, trying to straighten it but only making a minor adjustment; shoulders sag as he avoids any upward glance. Mouth remains tightly closed. No speaking. Ambient Motion: A faint ripple of light plays across his suit from overhead fluorescents; the tie fabric twitches and settles; perspiration beads at his temple; dust motes drift in the glow. End on his fingers resting against the knot, eyes downcast, ready for a cut out.",
      "rationale": "A slow push-in and micro-movements focus on embarrassment and deflation, closing the sequence on Saul’s diminished presence and the tie as a visual emblem of his insecurity."
    }
  ]
}
```
