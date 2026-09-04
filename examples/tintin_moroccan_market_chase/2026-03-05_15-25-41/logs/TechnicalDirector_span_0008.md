# Agent: TechnicalDirector
- **Span ID**: span_0008
- **Trace ID**: 2bdd77fb27b84af1
- **Session ID**: dataset_tintin_moroccan_market_chase_2026-03-05_15-25-41
- **Timestamp**: 2026-03-05 15:31:09
- **Duration**: 89.58s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 6398
- **completion_tokens**: 8510
- **total_tokens**: 14908

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
- **LOCATION LOCK**: Moroccan market district, North Africa (NOT European city)
- **ERA LOCK**: Daytime chase, contemporary with vintage tech
- **FORBIDDEN ELEMENTS**: European cobblestone squares, rainy weather, snow, modern glass skyscrapers, nighttime neon signage
- **STYLE OVERRIDES**:
  * color_palette: warm ochres, terracotta, bright produce colors, sun-bleached neutrals
  * architecture: Moroccan medina stalls, narrow alleys, textiles and wooden kiosks
  * lighting: harsh midday sun, hard shadows, dusty air bloom

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above co
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_reporter_blazes_market",
      "characters_in_shot": [
        "char_young_reporter",
        "char_bearded_companion"
      ],
      "character_appearances": {
        "char_young_reporter": "Young male, light shirt with sleeves rolled, trousers, leather boots and goggles; dust-streaked face, jaw set, focused rider ready to burst forward",
        "char_bearded_companion": "Rugged bearded man, utility jacket, trousers, boots and protective goggles; coated in dust, anxious but determined, crouched with a heavy launcher"
      },
      "t2i_template": "Stylized realism, kinetic chase framing, sun-baked palette. Lighting: harsh midday sun carving hard shadows; warm dust bloom hanging in the air. At <loc_ext_moroccan_market>, <prop_vintage_motorcycle_sidecar> fills center foreground from a low, slightly ahead-left angle, tilted toward a tight alley. <char_young_reporter> sits left in the saddle, body pitched forward over the bars, gloved hands poised on throttle and clutch, eyes locked straight down the alley. In the sidecar frame-right, <char_bearded_companion> compresses his shoulders, elbows tucked, <prop_bazooka> hoisted but not yet swinging, its tube intruding into frame-right foreground. Eyelines: <char_young_reporter> fixes the path ahead; <char_bearded_companion> darts glances between the tube’s sights and flanking stalls. Power dynamic: <char_young_reporter> commands the vector and speed; <char_bearded_companion> visually dominates frame-right with the oversized weapon, adding chaotic tension. Environment: narrow medina passage lined with wooden kiosks and textiles, stacked produce at <prop_fruit_stands> crowding the edges, pedestrians already parting; heat haze hints in the distance.",
      "i2v_template": "Low vehicle-mounted tracking move, camera ahead-left at bumper height, hugging the ground as it matches and slightly leads <prop_vintage_motorcycle_sidecar>. <char_young_reporter> twists the throttle and leans into the lane, shoulders tight; his goggles tilt as he steals a micro-glance toward the sidecar before refocusing ahead. <char_bearded_companion> swings <prop_bazooka> in jittery arcs frame-right, trying to steady the sights without pointing at bystanders; he braces his feet as the sidecar jitters over uneven boards. Mouth remains tightly closed. No speaking. Ambient motion: textiles whip across the alley, vendors jerk back, baskets wobble, a plume of dust and paper scraps streams off the wheels, sunlight strobing through latticework. The camera keeps the low, ahead-left perspective as the bike bears down on clustered <prop_fruit_stands> filling the path, ending with them looming large to set up the cut into the POV smash.",
      "rationale": "Low, slightly leading vehicle mount sells speed and urgency of a rising-tension beat while foregrounding the bazooka’s chaotic presence. Hard noon light and dusty bloom emphasize North African heat and grit. Ending on fruit stalls primes the smash POV of the next shot."
    },
    {
      "shot_id": "shot_02_fruit_stands_explode",
      "characters_in_shot": [],
      "character_appearances": {},
      "t2i_template": "High-energy POV composition with saturated produce colors against warm ochres. Lighting: harsh midday sun, crisp shadows, fine dust shimmering. From the POV of <prop_vintage_motorcycle_sidecar> rushing through <loc_ext_moroccan_market>, <prop_fruit_stands> crowd both sides of the frame in the near foreground, their wooden slats flexing, crates stacked precariously and teetering. At center ahead, a lattice of crates hangs in the path, oranges piled high at the top edge of the stack; a faint hint of handlebars and the top of the headlamp sits at the extreme bottom frame but the road dominates the view. The exact split-second before contact: the front crates vibrate on their nails, oranges closest to the edge just starting to roll forward but not yet airborne. Alley textiles flutter, casting hard-edged shadow stripes across the route.",
      "i2v_template": "Rapid forward POV with a touch of handheld bounce as the camera punches into the line of <prop_fruit_stands>. Crates splinter open in a shower of slats; <prop_oranges> explode toward the lens, tumbling and spinning in all directions, a few slamming straight at camera. Mouth remains tightly closed. No speaking. Ambient motion: splinters and packing straw whirl past, fabrics rip free and sail overhead, dust puffs into the sun-beam; a brief smear of crushed orange juices across the lens before it clears in the airstream. As debris parts, the camera finds an improvised <prop_debris_ramp> dead ahead in the alley, beginning a slight upward tilt to lead into the launch.",
      "rationale": "POV maximizes chaos escalation by putting the viewer in the rider’s path; fruit and debris flying at lens sells immediacy. Ending with ramp visible sets a natural bridge to the launch shot."
    },
    {
      "shot_id": "shot_03_bike_launches_debris",
      "characters_in_shot": [
        "char_young_reporter",
        "char_bearded_companion"
      ],
      "character_appearances": {
        "char_young_reporter": "Young male, light shirt sleeves rolled, trousers, boots, goggles; dust-streaked, focused, rising off the saddle onto pegs to commit to the jump",
        "char_bearded_companion": "Rugged bearded man, utility jacket, goggles and boots; tense, gripping sidecar rails with <prop_bazooka> hugged forward, bracing for impact"
      },
      "t2i_template": "Adventurous widescreen composition with sun-scorched tones and saturated market colors. Lighting: hard noon sun, deep shadow pockets, dust bloom catching light. In <loc_ext_moroccan_market>, a low-angle long shot frames <prop_debris_ramp> assembled from toppled wooden crates, boards, and torn fabrics at center midground. <prop_vintage_motorcycle_sidecar> is lined up in center foreground, front wheel just compressing the last boards but not yet leaving the ramp. <char_young_reporter> stands on the pegs, hips back, knees bent, arms taut on the bars, eyes locked forward along the launch path. In the sidecar, <char_bearded_companion> leans back to brace, <prop_bazooka> clutched and pointed forward but steady, gaze flicking from the ramp crest to the tube’s mouth. Power dynamic: <char_young_reporter> radiates control and commitment; <char_bearded_companion> occupies space with the weapon yet yields to the rider’s decisive posture. Bystanders and kiosks flank the narrow alley, textiles strung overhead fluttering in the heat.",
      "i2v_template": "Low crane-up follow: the camera rides just ahead and below the front wheel, then ascends with the arc as <prop_vintage_motorcycle_sidecar> surges up <prop_debris_ramp>. <char_young_reporter> yanks slightly on the bars and shifts weight back, the suspension decompressing as the front wheel lifts; he keeps his gaze forward, jaw tight. <char_bearded_companion> squeezes the rails and hugs <prop_bazooka> to keep it aimed downrange; the tube wobbles a hair as the sidecar leaves the ramp, then steadies as he locks his elbows. Mouth remains tightly closed. No speaking. Ambient motion: fabric banners snap as the bike passes underneath, dust and straw trail off the ramp, loose fruit bits ping away; harsh sunlight rakes across as the camera rises, revealing more sky. The move reaches the apex with the sidecar occupant prominent, framing his face and the tube to flow into the next close-up.",
      "rationale": "Low-to-high crane accentuates height and suspense peak. The composition hands off focus from the leap to the sidecar gunner for the CU beat, maintaining kinetic continuity."
    },
    {
      "shot_id": "shot_04_bazooka_accidental_fire",
      "characters_in_shot": [
        "char_bearded_companion"
      ],
      "character_appearances": {
        "char_bearded_companion": "Rugged bearded man, utility jacket and goggles; midair tension, shoulders hunched, eyes wide in shock as finger tightens on the trigger"
      },
      "t2i_template": "Close, canted composition for sudden-shock. Lighting: hard sun bleaching highlights; dusty air softens the edges. The frame isolates <char_bearded_companion> at center foreground, torso twisted with tension, eyes huge and fixed past the sights. <prop_bazooka> dominates frame-left foreground, its mouth aimed downrange; his trigger finger is compressed against the trigger but has not yet broken the shot. Eyeline: he stares through the sight line, not blinking. Power dynamic: the weapon visually overpowers, crowding the frame while he shrinks behind it, bracing. Background is an abstracted blur of sky and sun-bleached textiles from <loc_ext_moroccan_market>, suggesting midair motion without pulling focus.",
      "i2v_template": "Static Dutch angle with recoil shake: <prop_bazooka> discharges in a bright muzzle flash at frame-left; backblast smoke jets rearward, and the tube snaps against <char_bearded_companion>’s shoulder as he recoils, mouth clamped, eyes flaring. Mouth remains tightly closed. No speaking. Ambient motion: hot wind tugs at his goggles strap and jacket collar; the blurred background streaks slightly with the midair movement as smoke lingers and curls behind. The rocket streaks off frame in the aim direction, leading the cut toward the distant target.",
      "rationale": "A tight Dutch CU amplifies shock and comedic panic while isolating the accidental discharge. Recoil shake sells impact; the rocket exit vectors the viewer toward the next ELS of the dam."
    },
    {
      "shot_id": "shot_05_dam_explosion_boom",
      "characters_in_shot": [],
      "character_appearances": {},
      "t2i_template": "Epic scale, sun-blasted landscape. Lighting: blinding midday sun with hard contrast and heat haze shimmer. In <loc_ext_distant_dam>, an extra-long shot frames the monolithic concrete face of the dam embedded in arid hills. The structure is intact; a faint incoming smoke trail converges toward the dam’s midsection but no detonation has occurred yet. The foreground is empty scrub; no markets or urban skyline intrude. The air wavers with heat, washing the colors to pale stone and sun-bleached tones.",
      "i2v_template": "Static wide that eases into a slow zoom-in as the rocket impacts: a forceful plume erupts from the dam’s face, rolling upward and outward in a billow of dust and debris. Mouth remains tightly closed. No speaking. Ambient motion: heat haze shimmers intensify around the blast; a few startled birds scatter from the cliffs; fine particulate drifts in the bright light. As the plume expands, water begins to surge through the breach and spillway, churning white against concrete, building momentum that barrels down-valley—framing holds on the growing outflow to motivate the impending flood cut.",
      "rationale": "The ELS establishes geography and consequence. Slow zoom heightens dread while keeping the frame free of market elements; plume and water onset cue the disaster about to reach the medina."
    },
    {
      "shot_id": "shot_06_flood_surge_pursues",
      "characters_in_shot": [
        "char_young_reporter",
        "char_bearded_companion"
      ],
      "character_appearances": {
        "char_young_reporter": "Young male, light shirt rolled sleeves, trousers, boots, goggles; drenched with sweat and dust, glancing back while gunning the engine, determined",
        "char_bearded_companion": "Rugged bearded man, utility jacket and goggles; gripping <prop_bazooka> tight in the sidecar, eyes wide with panic as water bears down"
      },
      "t2i_template": "Sun-scorched chaos with kinetic framing. Lighting: harsh midday sun, hard-edged shadows, dust turning to mist in humid air. A reverse-mounted long shot races backward through <loc_ext_moroccan_market> alleys, framing <prop_vintage_motorcycle_sidecar> center foreground charging toward camera. <char_young_reporter> leans forward, right hand ready to punch the throttle, head turned just enough to glan
...
```
