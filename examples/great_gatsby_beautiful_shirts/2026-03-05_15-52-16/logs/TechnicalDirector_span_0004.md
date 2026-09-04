# Agent: TechnicalDirector
- **Span ID**: span_0004
- **Trace ID**: 45d29e4d81744584
- **Session ID**: dataset_great_gatsby_beautiful_shirts_2026-03-05_15-52-16
- **Timestamp**: 2026-03-05 15:56:06
- **Duration**: 78.79s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4893
- **completion_tokens**: 6109
- **total_tokens**: 11002

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
- **LOCATION LOCK**: North Shore, Long Island, New York, USA
- **ERA LOCK**: Early 1920s Jazz Age America
- **FORBIDDEN ELEMENTS**: modern technology, smartphones, contemporary casualwear, minimalist interiors, mid-century or later design cues
- **STYLE OVERRIDES**:
  * color_palette: soft pastels with warm sunlight
  * lighting: diffused natural daylight, glowing highlights
  * set_decoration: sumptuous, high-end 1920s luxury

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` fi
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_gatsby_tosses_shirts",
      "characters_in_shot": [
        "char_gatsby"
      ],
      "character_appearances": {
        "char_gatsby": "Male, early 30s, pastel silk shirt with crisp trousers and polished oxfords, exhilarated showman poised on the wardrobe balcony"
      },
      "t2i_template": "Opulent Jazz Age glamour with soft pastels and warm sunlight. Diffused natural daylight with glowing highlights pours through <prop_massive_windows>. Low-angle long shot inside <loc_int_gatsbys_bedroom>: <char_gatsby> stands on the upper rail of <prop_open_wardrobe> at background_upper_center, torso pitched forward, arms brimming with <prop_pastel_shirts>. His wrists tilt as the top layer begins to slip, but nothing has left his hands yet. Chin lifted, eyes fixed downward toward <prop_plush_bed> in the foreground; he commands the vertical space from balcony to bed. The wardrobe balcony remains clearly visible behind him. Below, the massive plush bed at foreground lower right lies pristine and expectant. Gauzy curtains at the sunlit windows stir faintly; dust motes sparkle in the beam, all poised at the brink of an extravagant release.",
      "i2v_template": "Camera: slow tilt up from <prop_plush_bed> toward the balcony, arcing to follow the descending path of <prop_pastel_shirts>. Action: <char_gatsby> unleashes the cascade with a theatrical flourish; his fingers open and flick, and the silks peel away in extreme slow-motion, sleeves puffing and panels unfurling. He leans over the rail, eyes tracking the drift, shoulders opening in presentation; his expression warms with contained delight. Reaction: no other characters visible. Lip constraint: Mouth remains tightly closed. No speaking. Ambient motion: <prop_massive_windows> curtains breathe on a gentle draft; dust motes drift; the bed’s coverlet ripples slightly where fabric is about to land; each shirt ripples and rotates, catching glowing highlights. Forward continuity: the tilt settles beneath the falling fabrics, holding the bed centered as the camera eases toward a higher vantage, ready to cut into the next overhead shot of the shirts settling.",
      "rationale": "Low-angle LS amplifies Gatsby’s performative power and spectacle. Slow tilt up and extreme slow-motion celebrate texture and wealth, aligning with exuberant display. The frame resolves toward a top-view composition to cut cleanly into the overhead fabric settling shot."
    },
    {
      "shot_id": "shot_02_shirts_fall_settle",
      "characters_in_shot": [],
      "character_appearances": {},
      "t2i_template": "Romantic stillness, sunlit pastels under diffused natural daylight with glowing highlights. Overhead medium close-up in <loc_int_gatsbys_bedroom>: a bouquet of <prop_pastel_shirts> hangs inches above <prop_plush_bed>, sleeves and collars suspended mid-swirl, not yet touching. Silk and linen textures gleam against a shallow depth of field. The bed’s plush surface centers the frame, unpressed and waiting. At background upper, the hazy glow of <prop_massive_windows> filters through gauzy curtains. No characters are visible; the poised fabric holds all attention in the split second before contact.",
      "i2v_template": "Camera: slow crane down in an overhead perspective, riding the drift of <prop_pastel_shirts> while keeping shallow focus on texture. Action: the shirts billow, fold, and glide in extreme slow-motion; collars flutter, buttons catch highlights; they ease down and alight in quiet waves on <prop_plush_bed>, air sighing out as fabric settles into soft, colorful heaps. Reaction: no characters on screen; voiceover from <char_daisy> is heard off-screen only. Lip constraint: Mouth remains tightly closed. No speaking. Ambient motion: sunlight blooms gently through <prop_massive_windows>; gauzy curtains lift and fall; dust motes dance in the glow; the bedding compresses and slowly rebounds where each shirt lands. Forward continuity: the crane eases to a near-static hold on the freshest pile centered in frame, inviting a cut to an eye-level close position where <char_daisy> will occupy the same mound in the next shot.",
      "rationale": "Aerial MCU isolates the tactile beauty of silk and linen, matching romantic awe. Shallow DOF and extreme slow-motion exalt texture. The final hold centers the mound to create a compositional bridge into Daisy’s intimate close-up."
    },
    {
      "shot_id": "shot_03_daisy_weeps_shirts",
      "characters_in_shot": [
        "char_daisy"
      ],
      "character_appearances": {
        "char_daisy": "Female, mid-20s, elegant 1920s couture with understated jewelry, seated amid pastel shirts on the bed, delighted then overwhelmed and tearful"
      },
      "t2i_template": "Soft, intimate eye-level close-up drenched in diffused natural daylight with glowing highlights; warm pastel palette in <loc_int_gatsbys_bedroom>. <char_daisy> sits centered on <prop_plush_bed>, cocooned by a halo of <prop_pastel_shirts> piled around her. Shoulders slightly forward, fingers clutching a handful of silk against her chest; her eyes shine, lips closed in a tremulous smile, breath poised at the edge of a laugh that has not yet escaped. Her eyeline dips to the fabric in her hands, then flicks up toward an unseen presence before returning down, revealing a flicker of conflict beneath delight. Behind, <prop_massive_windows> bloom softly through gauzy curtains, isolating her in opulent textures.",
      "i2v_template": "Camera: slow dolly in at eye level, compressing to an intimate close on <char_daisy>'s face and hands. Action: her shoulders quiver with a stifled, silent laugh; the smile falters; eyes well and then a few luminous tears slip free as she folds forward, burying her face into <prop_pastel_shirts>. Her fingers knead the silk, drawing it close; breath becomes shallow and tremulous as she stills. Reaction: she remains huddled in the fabric, trembling softly. Lip constraint: Mouth remains tightly closed. No speaking. Ambient motion: gauzy curtains at <prop_massive_windows> drift in the daylight; dust motes glint and drift; loose hems of the shirts flutter and settle; the mattress compresses subtly under her movement. Forward continuity: the dolly comes to rest on a tight frame of her head bowed into the shirts, holding long enough for a gentle linger or dissolve.",
      "rationale": "Eye-level CU preserves intimacy and vulnerability as delight collapses into sorrow. Soft, luminous tears and shallow ambient motion maintain the romantic-yet-melancholic tone. The final held pose offers a natural linger or dissolve to conclude the beat."
    }
  ]
}
```
