# Agent: TechnicalDirector
- **Span ID**: span_0007
- **Trace ID**: 93be579204aa4a52
- **Session ID**: dataset_BetterCallSaul3_2026-03-05_09-12-46
- **Timestamp**: 2026-03-05 09:19:07
- **Duration**: 202.98s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 11144
- **completion_tokens**: 15083
- **total_tokens**: 26227

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
- **LOCATION LOCK**: Albuquerque, New Mexico, USA — sun-baked urban arterial street (NOT coastal, NOT European/Mediterranean)
- **ERA LOCK**: Contemporary (2020s) — summer, midday (NOT historical period)
- **FORBIDDEN ELEMENTS**: Mediterranean/European architecture (stone villages, Venetian canals, gondolas), Old European cobblestone streets, Olive trees, Ocean, beach, boardwalk, coastal scenery, Rain, snow, puddles, wet asphalt, umbrellas, Golden-hour or nighttime lighting, Vintage cars (pre-1990 classics), UK/EU license plates, right-hand drive vehicles, double-decker buses, Non-English-only signage (e.g., Mandarin-only billboards), Police on-scene, squad cars, sirens, arrests, Ambulance/gurney/EMT medical intervention, Graphic injury or blood
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_saul_drives_street",
      "characters_in_shot": [
        "char_saul"
      ],
      "character_appearances": {
        "char_saul": "Older man, sun-faded short-sleeve button-down and dusty slacks, seated behind the wheel, sweaty brow, focused and wary"
      },
      "t2i_template": "Gritty handheld realism at eye level under high-noon harsh sunlight. <prop_battered_yellow_compact_car> with a mismatched red door tracks center frame, aligned mid-lane, windshield fully intact. Through the glass, <char_saul> sits upright with both hands on the wheel, shoulders squared, squinting ahead; jaw tight, intent on the road. Eyeline: <char_saul> scans forward, no visible engagement with anyone else yet, owning the small interior space while the wide street dominates around him. Environment: a wide Albuquerque arterial with heat haze, asphalt grays, low-rise stucco and brick storefronts with English/Spanish signage at the parking-lot edges, clear sky, short shadows.",
      "i2v_template": "Handheld tracking parallel along the curb with slight bob and vibration as the car moves left-to-right. <char_saul> makes micro-adjustments on the wheel, a quick glance to the side mirror then back to the road, shoulders subtly flexing with the bumps. Mouth remains tightly closed. No speaking. Ambient motion: heat shimmer ripples, glare skates across the intact windshield, a few contemporary US sedans with US license plates drift in the opposite lane, roadside dust kicks up and trails briefly. End with the lens drifting toward the windshield centerline, setting up a cut into an interior POV for the impending impact.",
      "rationale": null
    },
    {
      "shot_id": "shot_02_teen_smashes_windshield",
      "characters_in_shot": [
        "char_teen_scammer"
      ],
      "character_appearances": {
        "char_teen_scammer": "Teen boy, graphic t-shirt, shorts, skate shoes, mid-air lunge toward the windshield, face tense with shock"
      },
      "t2i_template": "Interior POV from the driver’s seat at eye level in harsh midday sun: the windshield is still intact, glare dicing across the glass. <char_teen_scammer> hangs mid-flight a split second from impact, arms tucked and knees bent, skateboard edge just dropping into the lower frame. Eyeline: <char_teen_scammer> locked on the glass, panic flickering. Power relationship: the incoming body dominates the frame, the car interior feels vulnerable. Environment glimpsed through the glass: sun-baked arterial, stucco storefronts, heat shimmer, short shadows.",
      "i2v_template": "Handheld jolt forward as the collision happens; <char_teen_scammer> slams onto the windshield, the board clips the hood and tumbles out of view. Cracks spiderweb explosively from the point of contact, safety glass granules tremble and sparkle in the sun. Mouth remains tightly closed. No speaking. Ambient motion: the whole cabin shakes, a wiper twitches, outside heat haze wobbles the strip beyond; the teen slides down out of frame, leaving a crazed lattice of cracks that become our fractured view. End with the POV settling through the shattered pattern toward the asphalt where the teen will land, motivating a cut to the exterior.",
      "rationale": null
    },
    {
      "shot_id": "shot_03_teen_screams_extortion",
      "characters_in_shot": [
        "char_teen_scammer",
        "char_scammer_friend"
      ],
      "character_appearances": {
        "char_teen_scammer": "Teen boy, scuffed graphic t-shirt and shorts, scraped and dusty, on hot asphalt gripping knee, overacting panic",
        "char_scammer_friend": "Teen boy, t-shirt, cap, skate shoes, crouched at the edge with smartphone raised, tense and intent"
      },
      "t2i_template": "Eye-level handheld MS under brutal midday sun. <char_teen_scammer> sprawls center foreground on the hot asphalt, one elbow propping him up as both hands hover over a bent knee, chest expanded a beat before shouting. Eyeline: he angles toward offscreen left where the driver would be. At frame right, <char_scammer_friend> leans in with <prop_smartphone> lifted, lens aimed at <char_teen_scammer> and the car beyond, shoulder tight and ready to bolt. Power dynamic: the phone’s gaze asserts pressure while the teen performs vulnerability. In background left, <prop_battered_yellow_compact_car> sits roadside with <prop_shattered_windshield> glittering; a skateboard lies nearby on the ground; heat shimmer washes the low-rise strip.",
      "i2v_template": "Handheld slight push-in on the teen. <char_teen_scammer> clutches his leg and thrashes for effect, head whipping toward offscreen left as he yells, “My leg! You broke my leg!” Mouth moves to match speech. <char_scammer_friend> creeps closer, tilting <prop_smartphone> to keep both the teen and the car in frame, darting anxious glances toward offscreen left anticipating confrontation. Ambient motion: hot air ripples, a contemporary SUV murmurs past in the distance with a US plate, grit and paper flecks skitter on the asphalt. End with the teen’s gaze snapping upward toward the left, creating space for an approaching figure to enter in the next shot.",
      "rationale": null
    },
    {
      "shot_id": "shot_04_saul_storms_out",
      "characters_in_shot": [
        "char_saul",
        "char_teen_scammer"
      ],
      "character_appearances": {
        "char_saul": "Older man, short-sleeve button-down and worn slacks, out of the car, wiry and furious, shoulders pitched forward, fists clenched",
        "char_teen_scammer": "Teen boy, on the ground propped on one elbow, wary and shrinking, hands near knee"
      },
      "t2i_template": "Low-angle handheld MLS in hard noon light. <char_saul> is mid-stride outside the open driver door of <prop_battered_yellow_compact_car> (the mismatched red door ajar), torso lunging toward <char_teen_scammer>. Eyeline: <char_saul> glares down at the teen; <char_teen_scammer> looks up from the ground, shoulders caved. Power dynamic: <char_saul> fills the near space, dominating; the teen occupies a smaller, vulnerable footprint frame right. The sun-baked arterial and stucco storefronts shimmer in the background.",
      "i2v_template": "Handheld follow surges after <char_saul> as he stomps forward, the loose door rocking on its hinges. <char_teen_scammer> scoots back on his palms, free hand lifting in a warding gesture, eyes wide. Mouth remains tightly closed. No speaking. Ambient motion: metal creaks, cicadas rasp, distant traffic hums, heat haze ripples over the asphalt. End with the camera dipping to frame <char_saul>'s leg drawing back near the teen’s knee, aligning for the low-angle impact in the next shot.",
      "rationale": null
    },
    {
      "shot_id": "shot_05_saul_kicks_knee",
      "characters_in_shot": [
        "char_saul",
        "char_teen_scammer"
      ],
      "character_appearances": {
        "char_saul": "Older man, short-sleeve shirt, sweat-damp, leg tensed mid-kick, face hard and unflinching",
        "char_teen_scammer": "Teen boy, hands wrapped around knee, bracing on elbows, startled and recoiling"
      },
      "t2i_template": "Low-angle MCU, harsh sunlight carving sharp-edged shadows. <char_saul>'s shin is cocked back, foot hovering inches from <char_teen_scammer>'s knee, weight forward and fingers splayed for balance. <char_teen_scammer> hunches defensively, hands clasping the supposedly broken knee, shoulders tight. Eyelines: <char_saul> glares down at the target; the teen's eyes dart to the incoming foot. The hot asphalt and heat haze vibrate around them.",
      "i2v_template": "Handheld whip-pan snaps into the moment of contact as <char_saul>'s foot drives into the teen's knee area; <char_teen_scammer> jerks backward in shock, palms slapping the pavement, the ruse faltering. Mouth remains tightly closed. No speaking. Ambient motion: a dull thud carries, dust puffs from the ground, a skateboard nearby rattles and rolls a few inches before settling. Finish with <char_saul> planting his foot and squaring up, torso turning toward both kids to set the eyeline for an imminent over-the-shoulders confrontation.",
      "rationale": null
    },
    {
      "shot_id": "shot_06_saul_taunts_lawyer",
      "characters_in_shot": [
        "char_teen_scammer",
        "char_scammer_friend",
        "char_saul"
      ],
      "character_appearances": {
        "char_teen_scammer": "Teen boy, t-shirt and shorts, shoulder foreground left, tense and defensive",
        "char_scammer_friend": "Teen boy, t-shirt, cap, skate shoes, shoulder foreground right, holding smartphone, skittish",
        "char_saul": "Older man, short-sleeve button-down, center midground, pointing, loud and commanding"
      },
      "t2i_template": "Over-the-shoulder framing from the kids: the shoulders of <char_teen_scammer> at left FG and <char_scammer_friend> at right FG rim the view, <prop_smartphone> lifted and pointed toward <char_saul> who stands center midground. Under harsh noon light, <char_saul> leans forward with a raised finger, chest filled, mouth just about to launch the taunt. Eyelines: <char_saul> drills straight at the pair; the kids hover backward, friend’s shoulder tightened as he aims the phone. <prop_skateboards> rest on the ground near their feet. The stucco strip and parking-lot edge bleach out behind in heat shimmer.",
      "i2v_template": "Handheld slight push-in toward <char_saul> through the kids’ shoulders. <char_saul> steps half a pace forward and delivers, jabbing a finger as he declares his line with relish. Mouth moves to match speech. <char_teen_scammer> and <char_scammer_friend> exchange a quick alarmed glance; <char_scammer_friend>’s grip on <prop_smartphone> wobbles, the framed image tilting as his nerve falters. Ambient motion: hot wind lifts shirt hems, distant engines drone, a skateboard wheel spins lazily then stops. End with the kids starting to pivot out of the OTS, telegraphing their imminent flight.",
      "rationale": null
    },
    {
      "shot_id": "shot_07_scammers_scramble_flee",
      "characters_in_shot": [
        "char_teen_scammer",
        "char_scammer_friend",
        "char_saul"
      ],
      "character_appearances": {
        "char_teen_scammer": "Teen boy, t-shirt and shorts, sprinting with skateboard clamped under arm, panicked",
        "char_scammer_friend": "Teen boy, t-shirt and cap, sprinting with skateboard under arm, looking over shoulder, rattled",
        "char_saul": "Older man, advancing with sharp strides in foreground, aggressive posture, predatory focus"
      },
      "t2i_template": "Eye-level handheld LS in blistering sun. <char_teen_scammer> and <char_scammer_friend> crouch a beat before launch, each gripping a skateboard, weight pitched forward toward frame right. In the foreground left, <char_saul> leans into the near space mid-advance, one arm extended, posture threatening. Eyelines: the kids glance back nervously at <char_saul> as they coil to flee; <char_saul> fixes on their escape route. Power dynamic: kids small and retreating, <char_saul> commands the foreground. The wide arterial and low-rise strip ripple with heat haze.",
      "i2v_template": "Handheld pan right whips to follow the kids as they explode into a sprint, boards tucked tight to their sides. <char_saul> lunges a couple of steps then checks himself, posture still aggressive as he slows near the curb. Mouth remains tightly closed. No speaking. Ambient motion: sneaker soles slap the hot pavement, skateboard wheels clatter against decks, distant traffic slides through the heat shimmer. End with the pan easing to a stop as the kids recede frame right, landing near the parked position of <prop_battered_yellow_compact_car> to motivate the return to the car-side angle.",
      "rationale": null
    },
    {
      "shot_id": "shot_08_saul_shouts_check",
      "characters_in_shot": [
        "char_saul",
        "char_teen_scammer",
        "char_scammer_frien
...
```
