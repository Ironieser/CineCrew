# Agent: TechnicalDirector
- **Span ID**: span_0006
- **Trace ID**: c3641556678d4269
- **Session ID**: dataset_pulp_fiction_briefcase_glow_2026-03-05_16-04-24
- **Timestamp**: 2026-03-05 16:12:38
- **Duration**: 177.96s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 9321
- **completion_tokens**: 11196
- **total_tokens**: 20517

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
- **LOCATION LOCK**: Shadowy interior room (urban apartment or warehouse), modern city, strictly indoors (NOT outdoors, NOT Mediterranean villa, NOT suburban living room)
- **ERA LOCK**: Contemporary modern era (1990s–2020s), timeless urban crime-noir
- **FORBIDDEN ELEMENTS**: Historical period dress (Victorian, 1920s, 1940s fedoras/trench coats), Vintage tech (CRT TVs, rotary phones, typewriters, payphones), Futuristic tech (holograms, AR UI, biometric scanners, LED matrix lighting), Neon cyberpunk color schemes (magenta/teal glow), Bright, high-key or flat lighting; white fluorescent overheads, Exterior views (windows showing daylight, city skyline, palm trees), Outdoor locations (streets, cars, alleys), Religious or supernatural depictions in
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_vincent_dials_case",
      "characters_in_shot": [
        "char_vincent"
      ],
      "character_appearances": {
        "char_vincent": "Adult man, tailored matte black suit with crisp white shirt and slim black tie; leaning over the briefcase, right hand poised on the combination dials; focused, controlled tension; unlit cigarette possibly present but mostly out of frame"
      },
      "t2i_template": "Neo-noir stillness at an extreme low-angle ECU on the lock: low-key chiaroscuro with cool desaturated shadows; a faint warm sliver breathes along the seam of <prop_black_briefcase>, lid shut. The combination dials sit misaligned. From frame right, <char_vincent>'s right hand hovers a millimeter above the knurled wheels, fingertips poised to begin the turn while his off-hand braces the case edge out of frame. Eyeline is angled downward—though his face is largely out of frame, his posture communicates intent and restraint. Power center is the briefcase lock dominating the frame; <char_vincent> intrudes as a precise, tense presence. The industrial interior falls into darkness with rapid falloff; shallow depth isolates the mechanism; a subtle haze rims the warm edge without revealing anything inside.",
      "i2v_template": "[Camera Move] Slow dolly-in from the extreme low angle, micro rack settling onto the dials. [Character Actions & Reactions] <char_vincent>'s fingertips land and rotate the wheels one by one: the first clicks into 6, the second into 6, the third into 6; his wrist flexes with measured precision, breath held. As the last number drops into place, the mechanism tightens and a hairline of warm light breathes at the seam of <prop_black_briefcase>; the lid remains closed. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] Sleeve fabric creases subtly; a faint smoky haze eddies near the seam; shallow focus breathes as the dials stop clearly on 6-6-6, setting up the imminent latch release.",
      "rationale": "An extreme low-angle ECU establishes the lock as the power object, heightening rising tension; micro-movements and chiaroscuro emphasize precision and control."
    },
    {
      "shot_id": "shot_02_latches_pop_open",
      "characters_in_shot": [
        "char_vincent"
      ],
      "character_appearances": {
        "char_vincent": "Adult man, tailored matte black suit with crisp white shirt and slim black tie; hand braced at the latch and lid edge; intent focus, breath held; cigarette unlit if glimpsed"
      },
      "t2i_template": "Low-angle close-up in noir chiaroscuro: <prop_black_briefcase>'s latch is centered, lid still closed, the combination wheels already aligned at 6-6-6. <char_vincent>'s thumb rests beneath the latch tab with tension coiled, fingertips curved over the lid edge ready to lift. His body leans in from frame right, eyeline and posture directed down at the mechanism. The warm seam glints faintly while the rest collapses into cool deep shadow; no interior is visible.",
      "i2v_template": "[Camera Move] Hold for a beat, then rack focus from the numbers to the latch as the camera adds a slight tilt up to follow the lid. [Character Actions & Reactions] A sharp metallic click as the latch snaps free; <char_vincent>'s thumb flips the tab and he eases the lid upward, hinge murmuring. A first, controlled spill of warm golden light collects along the opening without showing the inside. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] The glow wavers against subtle haze; soft shadows crawl over <char_vincent>'s knuckles; shallow depth blooms along the lid as it rises just enough to motivate the next reveal.",
      "rationale": "We emphasize the precise latch release to punctuate the reveal beat; controlled light spill keeps mystery while propelling pace."
    },
    {
      "shot_id": "shot_03_golden_light_spills",
      "characters_in_shot": [
        "char_vincent"
      ],
      "character_appearances": {
        "char_vincent": "Adult man, tailored matte black suit with crisp white shirt and slim black tie; upper body leaning toward the open case; eyes widening with awe; unlit cigarette clenched lightly between lips"
      },
      "t2i_template": "Pre-surge tableau at a low-angle medium-long: <prop_black_briefcase> sits foreground center with its lid just cracked, inner edge brightening but not yet pouring; <char_vincent> hovers in center midground, shoulders hunched and drawn forward, gaze locked into the opening; <prop_unlit_cigarette> rests still between his lips. The case anchors the frame like a magnet; <char_vincent> is pulled into its orbit. Cool, near-black surroundings fall away while a hesitant warm rim along the lid hints at the coming flood; gentle haze gathers close to the case without visible particles.",
      "i2v_template": "[Camera Move] Slow, deliberate dolly-in from the low angle toward the open case and <char_vincent>. [Character Actions & Reactions] The lid clears another inch and a warm golden light swells, spilling across the surface and climbing into <char_vincent>'s face; he leans closer, pupils dilate, shoulders slacken then freeze in awe; <prop_unlit_cigarette> rides a minute tremor at his lips, staying unlit. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] The glow expands with rapid falloff into black; hazy air shifts subtly with no distinct particles or beams; lapels and tie edge breathe; end with his face approaching the opening, aligning to cue an inside-the-case POV next.",
      "rationale": "We widen to feel the room respond to the light, then drive inward to transition the axis for the POV while maintaining mystery."
    },
    {
      "shot_id": "shot_04_vincent_bathed_meson",
      "characters_in_shot": [
        "char_vincent"
      ],
      "character_appearances": {
        "char_vincent": "Adult man, tailored matte black suit; face close and centered, bathed in warm glow; eyes dilating, expression slackening into trance; unlit cigarette between lips"
      },
      "t2i_template": "Interior POV from within <prop_black_briefcase>; frame edges vignetted to near-black, implying a narrow aperture. Suspended at the threshold, <char_vincent>'s face fills center foreground, skin caught in the warm glow; his eyes are on the verge of widening, pupils deep. <prop_unlit_cigarette> sits steady between his lips. He stares directly into the aperture—into us—while the world behind collapses to black. The perspective places him leaning in, drawn and supplicant to the unseen contents.",
      "i2v_template": "[Camera Move] Subtle inward push from the interior POV, maintaining low-angle alignment on <char_vincent>'s face. [Character Actions & Reactions] His eyes widen by degrees; micro-muscles in brow and cheeks relax; he tilts infinitesimally closer; the cigarette quivers a hair yet remains unlit; he holds the gaze without blinking for a beat. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] The warm glow breathes gently across his skin; faint haze pools at the vignetted edges; slow chest rise and a soft cloth rustle are visible; finish with a minute shoulder shift that opens an over-the-shoulder line for the next shot.",
      "rationale": "An inside-the-case POV heightens hypnosis and preserves the mystery by never showing interior contents; micro-expression sells mesmerized stillness."
    },
    {
      "shot_id": "shot_05_voice_we_happy",
      "characters_in_shot": [
        "char_vincent"
      ],
      "character_appearances": {
        "char_vincent": "Adult man, tailored matte black suit; shoulder and cheek in low-angle silhouette for an OTS; transfixed, listening; unlit cigarette at lips catching edge glow"
      },
      "t2i_template": "Over-the-shoulder low-angle setup from behind <char_vincent>'s left shoulder: the open <prop_black_briefcase> sits center foreground emitting a controlled warm pool; <char_vincent>'s cheek and shoulder edge silhouette the left of frame, head angled toward the case; <prop_unlit_cigarette> protrudes slightly. The surrounding room remains swallowed in black. An instant of taut silence hangs before an unseen presence speaks from off-screen.",
      "i2v_template": "[Camera Move] Static camera holds the OTS composition. [Character Actions & Reactions] An unseen <char_off_screen_voice> cuts through with an authoritative, probing line: \"We happy?\" off-screen. <char_vincent> barely reacts—eyes flicker, a slow nasal inhale, chin dips a hint—yet his gaze remains locked on the glow and posture stays entranced. [Lip Constraint] Mouth remains tightly closed. No speaking. [Ambient Motion] The golden light ripples faintly across his jawline and the case rim; haze shimmers near the lid; deep shadows stay undisturbed; hold the frame to cue a tighter reply.",
      "rationale": "Keeping the speaker unseen preserves menace; the OTS frames Vincent inside the glow’s influence while maintaining mystery."
    },
    {
      "shot_id": "shot_06_vincent_affirms",
      "characters_in_shot": [
        "char_vincent"
      ],
      "character_appearances": {
        "char_vincent": "Adult man, tailored matte black suit; low-angle close-up bathed in warm glow; gaze fixed into the case; softly speaking with minimal movement; unlit cigarette between lips"
      },
      "t2i_template": "Low-angle close-up held in noir contrast: <char_vincent>'s face centers the frame, wrapped in a warm golden glow; the defocused edge of <prop_black_briefcase>'s lid softens the bottom of frame as a light source cue. <prop_unlit_cigarette> rests between his lips. He is poised to answer—lips gently together, eyes anchored into the case, breath held in quiet resolve while the room behind remains near-black.",
      "i2v_template": "[Camera Move] Slow dolly-in inches closer, keeping the shallow depth on his eyes. [Character Actions & Reactions] <char_vincent> exhales a hushed affirmation: \"Yeah... we happy.\" His lips form each word with minimal motion; eyes never leave the glow; the cigarette remains unlit and steady. After the final word, his jaw softens and he holds the gaze. [Lip Constraint] Mouth moves to match speech. [Ambient Motion] The glow pulses almost imperceptibly; a faint wisp of haze drifts; a loose hair and tie tip barely stir; end on a held, centered close-up for a clean out.",
      "rationale": "A tight, low-angle CU isolates the quiet resolution; restrained performance and motivated glow keep the hypnotic tone."
    }
  ]
}
```
