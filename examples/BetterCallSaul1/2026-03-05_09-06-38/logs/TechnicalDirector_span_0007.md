# Agent: TechnicalDirector
- **Span ID**: span_0007
- **Trace ID**: 6d523fb0ca7d4e1f
- **Session ID**: dataset_BetterCallSaul1_2026-03-05_09-06-38
- **Timestamp**: 2026-03-05 09:10:59
- **Duration**: 94.92s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 5910
- **completion_tokens**: 7758
- **total_tokens**: 13668

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
- **FORBIDDEN ELEMENTS**: Do not introduce vibrant full-color except the television screen, No sunny weather; maintain heavy snowstorm atmosphere, No tropical or Mediterranean elements
- **STYLE OVERRIDES**:
  * color_palette: High-contrast black and white with isolated saturated color from TV
  * lighting: Harsh fluorescent in bakery; dim apartment lit by TV glow
  * season: Winter snowstorm

⚠️ These constraints OVERRIDE any default associations in your training data.
For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.

📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.
The `consistency_constraints` field MUST contain:
  - FORBIDDEN: Do
...
```

## Raw Response

```json
{
  "shots": [
    {
      "shot_id": "shot_01_gene_kneads_nervously",
      "characters_in_shot": [
        "char_gene"
      ],
      "character_appearances": {
        "char_gene": "Male, middle-aged, plain bakery attire with apron, shoulders hunched and tense, anxious focus with darting eyes"
      },
      "t2i_template": "Noir, high-contrast black-and-white still at a harshly lit stainless counter inside <loc_int_mall_bakery_kitchen>. High-angle MCU frames <char_gene> centered foreground: shoulders rounded, elbows tucked, hands hovering just above <prop_bakery_dough> with fingertips barely touching, about to press but not yet. His jaw is tight; behind thick glasses his eyes angle toward background right, checking the idle <prop_industrial_mixer>, then back to the dough—caught in the instant before another mechanical knead. The high angle imposes the sterile kitchen’s dominance; <char_gene> appears small and contained within rigid lines. Environment is stark: polished counter edges, the silent <prop_industrial_mixer> sits background right; no windows, no exterior cues.",
      "i2v_template": "Slow dolly in from the high angle toward <char_gene>. He presses down and folds <prop_bakery_dough> in precise, repetitive motions; his eyes flick left, then right, then down to his hands, a small shoulder twitch at a distant clank before rhythm resumes. Mouth remains tightly closed. No speaking. Fluorescent lights hum with a faint flicker; ventilation stirs the edge of his apron; the idle <prop_industrial_mixer> vibrates imperceptibly on its feet; fine flour dust motes drift through the light. End with the dolly settling closer on his tense face and hands, ready to cut away from this confined routine.",
      "rationale": "A high-angle dolly-in emphasizes the oppressive, sterile routine and <char_gene>’s anxiety. Harsh fluorescent lighting strengthens the noir dread while keeping the kitchen fully monochrome."
    },
    {
      "shot_id": "shot_02_returns_snowbound_home",
      "characters_in_shot": [
        "char_gene"
      ],
      "character_appearances": {
        "char_gene": "Male, middle-aged, drab winter coat with trace snow on shoulders, weary posture, cautious movements"
      },
      "t2i_template": "Noir, high-contrast black-and-white interior at eye level in <loc_int_gene_apartment>. Wide static frame: the door hangs ajar at frame left, a narrow wedge of faint snow-muted spill tracing the threshold. <char_gene> is half inside, one foot still at the sill, hand gripping the knob, shoulders slumped; damp specks of snow cling to his coat. His eyeline is low toward the floor as if measuring silence before committing to enter. In the dim room beyond, <prop_television> sits dark at background center and <prop_worn_out_couch> slumps background right; the space feels cavernous and swallowing, dwarfing him.",
      "i2v_template": "Static camera. <char_gene> steps fully in, shoulders sinking as he eases the door shut with a muted thud; a few flecks of snow fall from his coat onto the floor as he steadies himself and exhales softly. Mouth remains tightly closed. No speaking. A thin draft of cold air dies as the seal closes; faint radiator ticks answer from somewhere off-frame while the snow-muted light fades, leaving him mostly silhouette. He turns his body toward <prop_television> and shuffles deeper into the dark room, setting up the approach to the couch and VCR.",
      "rationale": "Eye-level, static wide isolates <char_gene> against a dim, swallowing apartment, conveying weary resignation. The door’s closure transitions from storm-battered exterior to interior quiet, preparing the ritual with the tape."
    },
    {
      "shot_id": "shot_03_sinks_inserts_vhs",
      "characters_in_shot": [
        "char_gene"
      ],
      "character_appearances": {
        "char_gene": "Male, middle-aged, drab winter coat sleeves and plain shirt visible, focused and deliberate, ritualistic calm over tension"
      },
      "t2i_template": "Noir, high-contrast black-and-white OTS at eye level from behind <char_gene> in <loc_int_gene_apartment>. His shoulder and cheek edge frame the left foreground. His right hand holds <prop_vhs_tape> aligned at the lip of <prop_vcr>’s open tray, the cassette hovering just before engagement—corner poised to enter but not yet pushed. His posture leans forward, elbows tight. Eyeline drops toward the slot, breath held. <prop_worn_out_couch> sags background left; the room is near-black, TV still off-screen and dark.",
      "i2v_template": "Rack focus from <char_gene>’s hand and <prop_vhs_tape> to the face of <prop_vcr> as he advances the cassette with a smooth, practiced push. The tray accepts it with a tactile clunk; rollers draw it inward as a soft whirr spins up. Mouth remains tightly closed. No speaking. Cloth rustles quietly; a faint, non-colored indicator glows in monochrome; dust motes drift in the minimal light. End with focus settled on the VCR transport engaging, framing the lower stack so the next cut can reveal the TV’s wake-up.",
      "rationale": "An OTS with rack focus ritualizes the act and centers the machine. Monochrome, minimal lighting preserves the pre-TV darkness and heightens the tactile, anticipatory moment."
    },
    {
      "shot_id": "shot_04_tv_color_burst",
      "characters_in_shot": [],
      "character_appearances": {},
      "t2i_template": "Noir, high-contrast setup in <loc_int_gene_apartment>: eye-level MS with <prop_television> centered foreground, screen dark and convex, a faint static sheen barely visible, and <prop_vcr> below mid-foreground, transport engaged. The room around it is near-black; no other light sources or color present. This is the breath before the first glow—power has engaged but the screen has not yet bloomed.",
      "i2v_template": "Slow dolly in toward <prop_television> as <prop_vcr> whirs to life; the CRT flickers from black to a brief gray scanline shimmer, then blooms into saturated color within the screen, casting a soft, isolated color spill onto adjacent surfaces while the rest of the room remains monochrome. Mouth remains tightly closed. No speaking. A gentle degauss thump ripples; static noise crawls at the edges; the transport hum steadies beneath. End with the screen filling more of frame, primed to cut into the ad content.",
      "rationale": "A forward move intensifies the moment the past intrudes via color. Keeping all color confined to the CRT preserves the project’s key visual contrast."
    },
    {
      "shot_id": "shot_05_saul_ad_shouts",
      "characters_in_shot": [
        "char_saul_goodman"
      ],
      "character_appearances": {
        "char_saul_goodman": "Young man, flashy suit with bright tie, energetic TV pitchman stance, aggressive confidence"
      },
      "t2i_template": "Inside the frame of <prop_television> at eye-level CU: <char_saul_goodman> fills the screen, shoulders squared, bright suit and tie saturated within the TV image. One hand is lifted mid-raise, poised to point directly at the lens; his mouth is set, about to open but not yet; eyes locked straight into camera with electric focus. The TV bezel and room beyond remain dark monochrome, isolating the vivid screen content.",
      "i2v_template": "Static camera locked on the CRT. <char_saul_goodman> snaps his finger-point toward the lens and launches into a rapid, energetic pitch, leaning in and chopping the air with his free hand as the ad drives forward. Mouth moves to match speech. Subtle CRT scanline shimmer and phosphor persistence play across the image; color saturation pulses slightly with editorial beats; faint speaker buzz and the underlying VCR whirr persist. End on his iconic held pose—finger extended at camera—ready to cut to the viewer’s reaction.",
      "rationale": "A static CU within the TV emphasizes the confrontational energy of the ad and the jarring return of color. The crisp CRT image becomes the singular color source in the monochrome room."
    },
    {
      "shot_id": "shot_06_gene_watches_silently",
      "characters_in_shot": [
        "char_gene"
      ],
      "character_appearances": {
        "char_gene": "Male, middle-aged, drab winter coat still on, seated, withdrawn, eyes fixed on screen with quiet ache"
      },
      "t2i_template": "Noir, high-contrast eye-level MCU in <loc_int_gene_apartment>. <char_gene> sits centered foreground, shoulders slightly caved; his face is mostly in monochrome shadow with a faint edge of anticipated glow along the cheek and glasses frame, just before full illumination. His eyes are locked toward the off-frame TV; lips pressed, expression held neutral and guarded in the instant before the color spill reaches him. The background falls into near-black.",
      "i2v_template": "Slow dolly in toward <char_gene> as the TV’s colored light swells across his features, sliding over his glasses and cheekbones; pupils tighten, a tiny swallow works his throat, and his breath rises shallowly without breaking the silence. Mouth remains tightly closed. No speaking. The color flicker plays across his lenses and skin while the rest of the room stays black; faint apartment creaks and distant storm hush persist; stray dust motes drift through the glow. End with a close, centered hold on his face lit by the TV, inviting a contemplative cut.",
      "rationale": "An intimate dolly-in lets the TV’s color transform his otherwise monochrome world, underscoring melancholic longing. Keeping the background near-black isolates his reaction."
    }
  ]
}
```
