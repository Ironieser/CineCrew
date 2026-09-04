# Agent: TechnicalDirector
- **Span ID**: span_0005
- **Trace ID**: 26897c809d8e48bb
- **Session ID**: dataset_iron_man_cave_forging_mask_2026-03-05_15-46-17
- **Timestamp**: 2026-03-05 15:51:15
- **Duration**: 125.88s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 6980
- **completion_tokens**: 7596
- **total_tokens**: 14576

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
- **LOCATION LOCK**: Subterranean cave forge, undetermined locale — DO NOT infer or depict a specific country, culture, or fantasy realm (NOT medieval Europe, NOT feudal Japan, NOT Norse, NOT dwarven/Tolkien).
- **ERA LOCK**: Atemporal, era-agnostic underground workshop — no overt historical markers (NOT medieval, NOT steampunk, NOT cyberpunk, NOT futuristic sci‑fi).
- **FORBIDDEN ELEMENTS**: Medieval castle architecture, Viking/Norse runes, Celtic knotwork, Samurai armor, kabuto, katana, Torii gates, Gothic arches or stained glass, Art Deco motifs, Roman columns or Greek statues, Renaissance paintings, Fantasy dwarven halls (Moria style), Elven motifs, Steampunk gears and brass goggles, Cyberpunk neon and holograms, Futuristic sci‑fi technology
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_forge_fire_glows",
      "characters_in_shot": [
        "char_blacksmith"
      ],
      "character_appearances": {
        "char_blacksmith": "Adult man, heavy leather apron over a grimy grey tank top, thick work gloves and worn work pants, sweat- and soot-smeared, standing rigidly over the anvil with shoulders slightly hunched and eyes locked downward; quiet dread and urgent focus in his posture"
      },
      "t2i_template": "Gritty industrial realism, high-contrast chiaroscuro; the only illumination is the fierce orange glow of <prop_forge_fire>. At eye level in a medium-long shot, <char_blacksmith> stands center-midground, torso angled over <prop_steel_anvil> in the center foreground. His gloved right hand hangs at his side with <prop_iron_hammer> gripped but lowered; his left hand steadies near the anvil edge. <prop_metal_mask> lies red-hot atop <prop_steel_anvil>, its edges shimmering with heat. Eyeline: <char_blacksmith> stares down at <prop_metal_mask>, shoulders subtly coiled as if bracing to begin. He dominates the center of frame, while the tools and glowing workpiece anchor the foreground. In the right background, the mouth of <prop_forge_fire> roars within <loc_int_cave_forge>, casting volatile light across rough stone walls and leaving deep blacks at the frame edges. Atmosphere: a taut, quiet dread hangs in the heat-hazed air, the moment suspended just before movement.",
      "i2v_template": "Static camera at eye level, holding a medium-long composition. <char_blacksmith> draws a slow breath; his chest rises and falls. His stance subtly adjusts as a boot scrapes gritty stone; his gloved fingers tighten around <prop_iron_hammer>, tendons flexing. He leans a fraction closer to <prop_steel_anvil>, gaze locked on <prop_metal_mask>, then begins to coil his shoulders, initiating the lift of the hammer from his side without yet bringing it above the work. Mouth remains tightly closed. No speaking. Ambient motion: <prop_forge_fire> flares and gutters, casting rhythmic pulses of orange across rough stone; heat ripples distort the air; a few ash motes drift through the light. Hold on the moment as the hammer just starts to rise into frame, setting up the cut to a low-angle, tighter view of the poised strike.",
      "rationale": "Establishes space and mood with a grounded, eye-level MLS; static framing and single-source firelight create quiet dread. Subtle preparatory motions motivate the cut into a tighter, more pressurized angle for the impending strike."
    },
    {
      "shot_id": "shot_02_hammer_raised_high",
      "characters_in_shot": [
        "char_blacksmith"
      ],
      "character_appearances": {
        "char_blacksmith": "Adult man, heavy leather apron over grimy grey tank top, thick work gloves, forearms veined and tense; sweat and soot streaks; hammer arm locked overhead, body poised and breath held in rising tension"
      },
      "t2i_template": "High-contrast, firelit chiaroscuro from <prop_forge_fire> as the sole source. Low-angle medium close-up pushes in on <char_blacksmith> at center foreground: his gloved hands grip <prop_iron_hammer> raised above <prop_metal_mask>, which glows atop <prop_steel_anvil> just below frame center. His elbows flare wide, shoulders braced, torso twisted slightly as he lines up the blow. Eyeline: <char_blacksmith> looks down past the hammer head directly to <prop_metal_mask>. The rough stone of <loc_int_cave_forge> recedes into darkness behind him. The moment is suspended with the hammer poised, a breath away from motion, the tension gathering but not yet released.",
      "i2v_template": "Slow dolly-in from the low angle, creeping closer to the raised hammer and clenched arms. <char_blacksmith>'s muscles quiver with the strain; a minute tremor in <prop_iron_hammer> settles as he aligns the head over <prop_metal_mask>. A bead of sweat crawls down his temple; his grip shifts a hair for precision; his chest tightens as he holds breath for the strike he is about to make. Mouth remains tightly closed. No speaking. Ambient motion: the glow from <prop_forge_fire> breathes brighter then dimmer, heat haze wavering; faint ash motes drift across the shallow depth of field. As the camera nears, he commits—initiating the downward swing without contact—freeze the last frame with the hammer just beginning its descent to set up a hard cut to the impact close-up.",
      "rationale": "Low-angle MCU and slow dolly-in amplify rising tension and physical effort, holding just before the strike to maximize anticipation and create a clean match cut into the impact close-up."
    },
    {
      "shot_id": "shot_03_sparks_violently_erupt",
      "characters_in_shot": [
        "char_blacksmith"
      ],
      "character_appearances": {
        "char_blacksmith": "Adult man, heavy apron and gloves, sweat-slick and soot-streaked face; jaw clenched, eyes narrowed with focus; mid-strike posture with explosive exertion as light from sparks sculpts his features"
      },
      "t2i_template": "Chiaroscuro close-up at eye level, the only light coming from <prop_forge_fire> and the imminent flare of impact. <prop_iron_hammer> hangs a hair's breadth above <prop_metal_mask> on <prop_steel_anvil> at frame center, frozen in the split second before contact. At frame left, part of <char_blacksmith>'s face and shoulder edge into view, eyes locked on the glowing target; his grip and forearm tense in a compressed coil of power. The rough stone and surrounding void of <loc_int_cave_forge> sink into deep black around the peripherals. The air seems to hold its breath: the hammer is about to land.",
      "i2v_template": "Static camera CU with a subtle micro-jolt at impact. <char_blacksmith> drives <prop_iron_hammer> down into <prop_metal_mask> on <prop_steel_anvil>; the instant of contact detonates a violent fan of bright orange sparks that flare across the frame, carving his sweat- and soot-streaked features into stark relief for a heartbeat. His shoulders compress with the blow, then rebound; eyes squeeze tighter, jaw locked. Mouth remains tightly closed. No speaking. Ambient motion: sparks arc outward, ricochet off stone, and rain in incandescent trails; fleeting heat shimmer ripples; tiny cinders drift and dim as they fall, while the glow from <prop_forge_fire> undulates behind the dying spray. End on the sparks fading and his face slipping back into shadow, holding the CU to allow a clean cut out.",
      "rationale": "A static CU with an impact judder preserves clarity for the explosive release; the spark burst becomes the lighting beat that reveals his fatigue and drive, then returns him to shadow for a dramatic button."
    }
  ]
}
```
