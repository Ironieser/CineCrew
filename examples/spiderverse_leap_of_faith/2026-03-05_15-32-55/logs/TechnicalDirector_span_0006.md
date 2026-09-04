# Agent: TechnicalDirector
- **Span ID**: span_0006
- **Trace ID**: 2cc9b254b5c04b25
- **Session ID**: dataset_spiderverse_leap_of_faith_2026-03-05_15-32-55
- **Timestamp**: 2026-03-05 15:38:19
- **Duration**: 91.07s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 5327
- **completion_tokens**: 7984
- **total_tokens**: 13311

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
- **LOCATION LOCK**: New York City, USA (NOT Los Angeles, NOT Tokyo)
- **ERA LOCK**: Contemporary urban setting
- **FORBIDDEN ELEMENTS**: Mediterranean architecture, daytime sunshine, pastoral countryside, period costumes, rural landscapes
- **STYLE OVERRIDES**:
  * color_palette: Neon blues, magentas, cyans; high-contrast blacks
  * architecture: Modern glass-and-steel skyscrapers; urban rooftops
  * cinematography: Comic-book framing, halftone textures, extreme angles, 180-degree inversion
  * frame_rate: Variable frame rates to emphasize emotion and motion

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_edge_breath_poise",
      "characters_in_shot": [
        "char_young_superhero"
      ],
      "character_appearances": {
        "char_young_superhero": "Masked young man, black suit beneath bright green jacket and red-and-blue high-top sneakers, toes over rooftop ledge; steadying breath, focused and apprehensive"
      },
      "t2i_template": "Stylized comic-book neon aesthetic with halftone textures and bold contrast; dutch-angled medium shot. Neon-lit night high-contrast rimlight with soft city-glow fill. <char_young_superhero> stands at the extreme edge of <loc_ext_new_york_skyscraper_rooftop>, positioned frame_right with the line of the ledge slicing diagonally; the toes of <prop_red_blue_sneakers> hang just beyond the edge. Posture: shoulders slightly forward, hands relaxed at sides, chest lifted as he gathers air; jaw tight, eyes fixed outward toward the vast city to frame_left. <prop_green_jacket> hems lift in the wind but have not yet whipped into full flutter. Eyeline runs past camera-left into the neon abyss; body is canted toward the void while the city expanse dominates negative space, emphasizing his smallness against the skyline. The atmosphere is tense and quiet—the held breath before commitment; glass-and-steel verticals recede toward frame_left, depth exaggerated by high-contrast blacks and neon rims.",
      "i2v_template": "[Camera Move] Slow dolly-in along the rooftop ledge plane at a dutch angle, tightening subtly on <char_young_superhero>'s profile with the edge anchored at frame_right. [Character Actions & Reactions] <char_young_superhero> inhales; chest expands beneath the jacket; fingers flex, then settle; a measured exhale mists briefly; weight shifts infinitesimally backward but heels remain planted; <prop_green_jacket> flutters with increasing amplitude; <prop_red_blue_sneakers> scrape lightly as grip adjusts. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] Neon signage glows and flickers across <loc_ext_new_york_skyscraper_rooftop>; distant traffic lights pulse and headlights drift; wind combs jacket fabric and hair fibers; faint haze and dust motes drift left-to-right; halftone texture shimmers subtly. End with camera nearly parallel to his profile, his center of mass tipped a fraction toward the drop, primed for a clean cut into the over-the-ledge descent of the next shot.",
      "rationale": "A dutch MS compresses intimacy and imbalance to externalize fear turning to courage. The slow dolly-in and rim-lit silhouette foreground the breath before action, setting spatial logic for the over-ledge transition."
    },
    {
      "shot_id": "shot_02_backward_fall_abyss",
      "characters_in_shot": [
        "char_young_superhero"
      ],
      "character_appearances": {
        "char_young_superhero": "Masked young man, black suit beneath bright green jacket and red-and-blue high-top sneakers, arching at the balance point on the ledge; arms close to body, resolute and calm"
      },
      "t2i_template": "High-angle long shot framed in bold neon halftones; low-key, high-contrast edges. The camera hovers just over the lip of <loc_ext_new_york_skyscraper_rooftop>, looking down into the city void. <char_young_superhero> is centered at the ledge, shoulders rolling back but weight not yet surrendered; arms still close to his sides; <prop_red_blue_sneakers> toes at the very threshold; <prop_green_jacket> begins to lift and peel from his torso. Rooftop glass-and-steel still occupies the top of frame as the city yawns toward frame_bottom-left. It is the tipping instant before he lets himself fall.",
      "i2v_template": "[Camera Move] Crane glides over the ledge and then tips down, committing into a drop-follow as the rooftop flips past the top of frame. [Character Actions & Reactions] <char_young_superhero> releases his heels; back arcs as he yields to gravity; arms fold in tight to streamline; chin points skyward; <prop_red_blue_sneakers> flash their white soles toward camera as they leave the ledge; <prop_green_jacket> whips hard, sketching cyan/magenta motion streaks along the fall vector. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] The ledge races out of frame; neon signs smear into vertical trails rising past him; wind roars past; grit and paper scraps spiral upward relative to his fall; neighboring tower facades slide by with parallax. End with the camera matching his velocity just above his chest and beginning a slight roll to cue the full 180-degree inversion in the next shot.",
      "rationale": "A high-angle crane over the edge transforms the ledge into a launch line and sells the surrender to gravity. The end-state roll seeds the upcoming 180-degree inversion to maintain kinetic continuity."
    },
    {
      "shot_id": "shot_03_world_inverts_rising",
      "characters_in_shot": [
        "char_young_superhero"
      ],
      "character_appearances": {
        "char_young_superhero": "Masked young man, black suit beneath bright green jacket and red-and-blue high-top sneakers, in freefall mid-orientation change; composed focus giving way to exhilaration"
      },
      "t2i_template": "Neon silhouette with halftone streaks; high-contrast backlight. Dutch-leaning medium close-up with the city glow behind on <loc_ext_new_york_skyscraper_rooftop>'s skyline. <char_young_superhero> is centered, still falling but the horizon has not yet flipped; shoulders tense, arms close to the torso; <prop_green_jacket> streams backward in thin ribbons of fabric. The air feels electrically charged—the split-second before the world violently inverts to make his fall read as ascent.",
      "i2v_template": "[Camera Move] Rapid 180-degree roll with a speed ramp: begin locked on <char_young_superhero>'s face and shoulders, then accelerate through the horizon flip while keeping him pinned center-frame. [Character Actions & Reactions] <char_young_superhero> continues freefall; jaw loosens, gaze lifts; shoulders relax; hands drift outward a few inches in nascent openness; <prop_green_jacket> trails, then snaps into the new orientation with neon rim edges sketching arcs during the roll. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] Window grids and neon bands whirl around him into a luminous halo; halftone speed lines streak with the rotation; variable frame rate strobes through the flip, then smooths as the rising illusion locks. End with the roll completed and the camera settling slightly below his chin so the city now slides downward behind him, setting a clean cut into the low undershot wide where his arms will fully spread.",
      "rationale": "The violent 180 roll externalizes the inner shift from fear to faith; pinning the hero while the world turns sells the psychological inversion and preps the low-angle reveal next."
    },
    {
      "shot_id": "shot_04_arms_wide_leap",
      "characters_in_shot": [
        "char_young_superhero"
      ],
      "character_appearances": {
        "char_young_superhero": "Masked young man, black suit beneath bright green jacket and red-and-blue high-top sneakers, freefall with arms poised to spread; serene, defiant resolve"
      },
      "t2i_template": "Low undershot long shot in bold neon halftones, high-contrast silhouette. The camera tracks from below as <char_young_superhero> hangs centered above against the city glow of <loc_ext_new_york_skyscraper_rooftop>'s skyline, still in freefall but not yet opening his arms; elbows remain tucked near his ribs; <prop_green_jacket> billows lightly without full span; <prop_red_blue_sneakers> point downward. Specular highlights skim across nearby glass surfaces as if tension is about to snap; the upward-moving city parallax sustains the illusion that he ascends.",
      "i2v_template": "[Camera Move] Stabilized low-angle tracking follow with a slow dolly-in toward <char_young_superhero>'s silhouette. [Character Actions & Reactions] <char_young_superhero> draws a breath and throws his arms wide in a decisive, expansive motion; chest opens; head tips back into the neon; <prop_green_jacket> blossoms into a winglike billow; <prop_red_blue_sneakers> extend with toes pointed as legs align with the fall. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] A crystalline echo ripples across reflections—specular highlights jitter and crawl along building glass as if shattering off-screen; neon glints skate across his suit; the city streams downward to enhance the rising illusion; thin cloud wisps pass the lens; tiny debris sparkles trail behind; motion blur eases as the frame rate calms into a steadier cadence. End holding on a centered, symmetrical rising silhouette with arms fully extended against magenta-cyan skyglow for a clean button or transition.",
      "rationale": "An undershot LS frames the hero as transcendent, letting the city fall past him while he opens up. Specular glass cues the aural beat without literal shards, maintaining the comic-book language."
    }
  ]
}
```
