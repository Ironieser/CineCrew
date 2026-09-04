# Agent: TechnicalDirector
- **Span ID**: span_0004
- **Trace ID**: 542f92ea31d54213
- **Session ID**: dataset_pulp_fiction_royale_with_cheese_2026-03-05_17-47-59
- **Timestamp**: 2026-03-05 17:51:20
- **Duration**: 67.72s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 4832
- **completion_tokens**: 5307
- **total_tokens**: 10139

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
- **LOCATION LOCK**: Los Angeles, California, USA (NOT New York, NOT Europe)
- **ERA LOCK**: 1990s America
- **FORBIDDEN ELEMENTS**: Mediterranean architecture, New York brownstones, nighttime lighting, European city streets, Italian countryside
- **STYLE OVERRIDES**:
  * color_palette: Warm California morning sunlight, strong contrast
  * architecture: Automotive interior only, no exterior landmarks
  * wardrobe: Crisp black suits, white shirts, narrow ties

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.

...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_sunlit_ride_smoke",
      "characters_in_shot": [
        "char_jules_winnfield",
        "char_vincent_vega"
      ],
      "character_appearances": {
        "char_jules_winnfield": "Adult man, crisp black suit, white shirt, narrow tie; seated frame-left in a tan leather car interior, relaxed posture with a cigarette poised to tap ash, calm and at ease",
        "char_vincent_vega": "Adult man, crisp black suit, white shirt, narrow tie; seated frame-right in a tan leather car interior, relaxed posture with a cigarette near his lips, composed and unhurried"
      },
      "t2i_template": "Style: Naturalistic 1990s neo-noir with minimalist palette inside <loc_int_moving_car>. Lighting: Warm California morning sunlight with strong contrast; shifting window patterns slice across faces and tan leather. Framing/Positions: <char_jules_winnfield> sits frame-left, shoulders loose, cigarette held just above the door line, ash elongated but not yet flicked; eyeline forward down the road. <char_vincent_vega> sits frame-right, cigarette hovering near his lips, cheeks relaxed as if poised to exhale but holding it a beat; eyeline also forward. Relational dynamics: Both share equal space, mirroring relaxed body language; an unspoken rhythm suggests easy companionship rather than dominance. Environment: The interior of <prop_vintage_car> envelopes them—tan leather, chrome trim and textured dash; windows show only abstract blur from motion, with no exterior landmarks visible; faint smoke hangs in the air.",
      "i2v_template": "Camera Move: Static camera locked to the interior of <loc_int_moving_car>, with subtle engine vibration and gentle bob in the frame. Character Actions & Reactions: <char_jules_winnfield> taps the ash with a small flick; a thin ribbon of ash falls and a lazy smoke coil lifts past his cheek, his gaze staying forward before beginning the slightest turn toward <char_vincent_vega>. <char_vincent_vega> exhales a smooth plume, ember brightening briefly, then lowers his hand, glancing ahead with a micro nod in sync with the car’s roll; as <char_jules_winnfield> begins to angle toward him, <char_vincent_vega> shifts his shoulders minutely to acknowledge. Mouth remains tightly closed. No speaking. Ambient Motion: Bands of sunlight and passing shadow sweep rhythmically across faces and seats; smoke wafts and disperses; reflections slide over chrome; blurred window motion stays abstract with no identifiable landmarks. Forward Continuity: End with <char_jules_winnfield> just initiating a turn toward <char_vincent_vega>, setting up the over-the-shoulder composition of the next shot.",
      "rationale": "A calm, balanced two-shot reinforces the relaxed-flow beat and establishes spatial geography. Static mount plus ambient vibration and moving light keep the frame alive without breaking the interior lock or revealing exteriors."
    },
    {
      "shot_id": "shot_02_jules_asks_question",
      "characters_in_shot": [
        "char_jules_winnfield",
        "char_vincent_vega"
      ],
      "character_appearances": {
        "char_jules_winnfield": "Adult man, crisp black suit, white shirt, narrow tie; centered in frame, leaned in slightly inquisitive with cigarette between fingers, mid-turn toward his partner, alert and curious",
        "char_vincent_vega": "Adult man, crisp black suit, white shirt, narrow tie; only right shoulder/head edge visible in the foreground, steady and relaxed, listening posture"
      },
      "t2i_template": "Style: Tight over-the-shoulder composition inside <loc_int_moving_car> with minimalist neo-noir realism. Lighting: Warm California morning sun with bold contrast; shifting window stripes rake across faces and shoulder line. Framing/Positions: <char_jules_winnfield> is centered in the mid-ground, chin tipped slightly toward the right, cigarette held between fingers near his chest; his lips are just parted as if about to speak but not yet. <char_vincent_vega>'s right shoulder and side of head frame the right foreground as a soft silhouette, anchoring the OTS. Eyelines/Power: <char_jules_winnfield> aims his gaze toward <char_vincent_vega> just off to camera-right, body leaning in a touch—assertive curiosity without aggression; the right-foreground shoulder remains steady, acting as a framing device. Environment: The tan leather and chrome of <prop_vintage_car> form the backdrop; windows show only abstract blurred motion with no landmarks.",
      "i2v_template": "Camera Move: Static OTS at eye level, gently breathing with road vibrations. Character Actions & Reactions: <char_jules_winnfield> completes his turn toward <char_vincent_vega>, brows lifting slightly as he raises the cigarette hand in a small conversational gesture; he asks his question, then holds the gaze. <char_vincent_vega>'s shoulder shifts subtly in acknowledgment; his head angle tilts a fraction as if preparing to respond, staying mostly off-screen. Mouth moves to match speech. Ambient Motion: Fleeting bands of sunlight and shadow travel over <char_jules_winnfield>'s face and the foreground shoulder; faint smoke wisps curl around his words; ash trembles with the car’s hum; blurred window motion remains abstract. Forward Continuity: End with <char_jules_winnfield> finishing his line on a micro-pause, while <char_vincent_vega>'s shoulder dips as if drawing breath—priming a cut to a tight CU on <char_vincent_vega>.",
      "rationale": "An eye-level OTS emphasizes conversational intimacy and Jules’s probing energy. Keeping Vincent in the foreground sustains spatial clarity and creates a visual bridge into Vincent’s upcoming close-up."
    },
    {
      "shot_id": "shot_03_vincent_voiceover_reply",
      "characters_in_shot": [
        "char_vincent_vega"
      ],
      "character_appearances": {
        "char_vincent_vega": "Adult man, crisp black suit, white shirt, narrow tie; tight close-up with a faint playful smirk forming, calm eyes catching shifting sunlight, cigarette low in frame with a soft ember"
      },
      "t2i_template": "Style: Tight CU minimalism inside <loc_int_moving_car>, naturalistic 1990s neo-noir. Lighting: Warm California morning sun with strong contrast; moving window patterns swim softly across <char_vincent_vega>'s face. Framing/Positions: <char_vincent_vega> centered; his eyes forward with a hint of amusement, lips closed a breath before speaking; the cigarette rests low at frame edge, ember glowing faintly. Focus Setup: Initial focus clings to a nearby chrome glint or ember-edge while <char_vincent_vega>'s face sits fractionally soft, inviting an impending rack. Environment: Tan leather and chrome of <prop_vintage_car> fill the background; windows show only abstract blur, no exterior landmarks.",
      "i2v_template": "Camera Move: Begin with a gentle rack focus from the ember/chrome detail to <char_vincent_vega>'s eyes; camera remains interior-locked with subtle road vibration. Character Actions & Reactions: As focus lands, <char_vincent_vega>'s mouth curves into a small smirk and he delivers the line with easy cadence, then lets the smile hang for a beat. Off-screen, the listening presence of <char_jules_winnfield> is implied but not shown. Mouth moves to match speech. Ambient Motion: Sunlight bands and soft shadows drift across his features; thin smoke threads rise and dissipate; chrome reflections creep across the dash; window motion stays abstract and landmark-free. Forward Continuity: End holding steady on <char_vincent_vega>'s eyes and lingering smirk, providing a clean button for the sequence.",
      "rationale": "A tight CU with a purposeful rack emphasizes the playful reveal and syncs with the dialogue rhythm. Keeping the frame interior-locked and landmark-free preserves the era/location constraints while focusing attention on the line delivery."
    }
  ]
}
```
