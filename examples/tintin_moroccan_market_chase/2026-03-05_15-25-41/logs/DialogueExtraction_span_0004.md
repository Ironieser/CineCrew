# Agent: DialogueExtraction
- **Span ID**: span_0004
- **Trace ID**: 2bdd77fb27b84af1
- **Session ID**: dataset_tintin_moroccan_market_chase_2026-03-05_15-25-41
- **Timestamp**: 2026-03-05 15:29:06
- **Duration**: 8.21s
- **Validation**: Success

## Metadata

- **model**: gpt-5-2025-08-07
- **provider**: azure
- **api_version**: 2024-02-15-preview

## Token Usage (Cost Tracking)

- **prompt_tokens**: 2267
- **completion_tokens**: 575
- **total_tokens**: 2842

## Input (preview)

```
In a sweeping, high-speed tracking shot through a vibrant, sun-baked Moroccan market, a young reporter with a signature quiff speeds forward on a vintage motorcycle with a sidecar. His bearded companion sits in the sidecar, wildly aiming a bazooka. They crash violently through colorful fruit stands, sending oranges flying directly into the lens. As the motorcycle launches into the air off a ramp of debris, the companion accidentally fires the weapon. A massive explosion hits a distant dam, and i...
```

## Prompt Rendered

```
=== System ===
You are a Script Supervisor extracting dialogue from a screenplay.

Task: Extract the exact dialogue spoken in this shot, identifying ALL speakers AND their dialogue targets.

CRITICAL RULES:
0. **SILENT SHOT DETECTION** (CHECK FIRST):
   - If subject_action describes PURE ACTION without dialogue cues → SILENT (full_dialogue empty, speaker_id "silent")
   - If subject_action contains "rebukes", "admonishes", "tells", "says", "exchanges remarks" → HAS DIALOGUE, search script
   - If multiple characters in entities → may have dialogue, search script

1. **Multi-Speaker Detection**: If multiple characters speak, identify EACH; use dialogue_lines with speaker_id, listener_id, text, order.

2. **Dialogue Target**: Infer listener using spatial cues, dialogue content, social relations, emotional intent, scene context, narrative intent.

3. **Special Listener IDs**: "audience" (monologue), "group" (3+ people), "multiple" (2+ specific), or char_id.

Character ID Mapping:


OUTPUT: full_dialogue, speaker_id, listener_id, is_multi_speaker, dialogue_lines, sentences.
Extract COMPLETE dialogue exchanges, not just the first line.



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



--- [KNOWLEDGE: rules/agents/dialogue_emotion.md] ---
# Dialogue & Emotion Rules (DialogueAllocator / DialogueExtraction)


---

## Dialogue Allocation

- **Shots with Dialogue**: MUST assign `dialogue`, `speaker_id`, `voice_id`, `emotion`.
- **Shots without Dialogue**: MUST infer pure visual emotion (`emotion` field cannot be empty).
- **Multi-Speaker**: MUST identify `speaker_id` for each line.

## Emotional Continuity

- **Scene-Level Tracking**: Consider emotional history of previous 3 shots.
- **Logical Progression**: Emotion changes must be logical (e.g. grief → desperation → anger).
- **Type Distinction**: Character emotion vs. environment emotion (`speaker_id = "environment"`).

## Language & Script

- **Preserve Original Dialogue Language**: The `dialogue`, `full_dialogue`, and each `dialogue_lines.text` MUST keep the same language as the original script.
- **Chinese Scripts**: When the source script is in Chinese, ALL dialogue-related fields MUST remain in Chinese; DO NOT translate them to English or any other language.
- **No Automatic Translation**: DialogueAllocator and related agents MUST NOT rewrite or translate dialogue content; they may only segment it, map speakers/listeners, and add emotion/metadata.

## Prohibited

- DO NOT skip emotion inference for dialogue-free shots (all shots have emotion).
- DO NOT ignore emotional history (must consider emotional continuity).

## Checklist (DialogueAllocator Output)

- [ ] All dialogue Segments contain `dialogue`, `speaker_id`, `voice_id`, `emotion`.
- [ ] All non-dialogue Segments contain `emotion` (pure visual inference).
- [ ] Reasonable emotion changes (no abrupt jumps).

-----------------------------



--- [L2: DialogueAllocatorAgent] ---
## 🎤 DialogueAllocatorAgent Specifications

### Dialogue Extraction Strategy

**LLM Prompt Structure**:
```
Given:
1. Master Shot description (shot intent, characters, actions)
2. Original script segment (may contain multiple scenes)

Task:
- Extract dialogue belonging to this shot
- Identify multi-speaker situations
- Output structured DialogueExtraction
```

**Schema**:
```python
class DialogueExtraction:
    has_dialogue: bool
    is_multi_speaker: bool  # Key: identify multi-person dialogue
    dialogue_lines: List[DialogueLine]  # speaker_id and text for each line

class DialogueLine:
    speaker_id: str  # Must be character ID from Asset Library
    text: str
```

### Emotion Inference Strategy

#### Dialogue-Based Emotion (For shots with dialogue)
**Context Input**:
1. Dialogue content
2. Visual context (lighting, composition, camera movement)
3. Emotional history (emotions from previous 3 shots)

**LLM Prompt Key Instructions**:
```
Infer emotion based on:
- Dialogue: "{dialogue}"
- Visual: {lighting}, {camera_angle}, {motion}
- History: [{emotion_history}]

Requirements:
- Consider emotional continuity (logical progression or maintenance)
- Select from tag library: grief, anger, fear, desperation, joy, ...
```

#### Visual Emotion (For shots without dialogue)
**Context Input**:
1. Lighting type (Chiaroscuro → tension)
2. Camera movement (Dolly in → intensifying)
3. Composition angle (Low angle → dominance)
4. Action description (Wedding → joy)
5. Motion Strength (high → chaotic, low → peaceful)

**Emotion Tag Library (Pure Visual)**:
`joyful`, `tense`, `melancholic`, `ominous`, `peaceful`, `chaotic`, `intimate`, `isolated`, `triumphant`

### Dialogue Relationship Inference

**New Fields**:
- `speaker_id`: Speaker ID
- `listener_id`: Listener ID (may be null)
- `dialogue_direction`: Dialogue direction description (e.g., "Bonasera speaking to Vito Corleone")

**Inference Strategy (Multi-Layer)**:
1. **Spatial Cues**: Camera position, angle, character placement
2. **Dialogue Content**: Forms of address, questions, imperative language
3. **Social Relations**: Hierarchical, family, friends
4. **Emotional Intent**: Request, command, comfort
5. **Scene Context**: Social structure of current scene
6. **Narrative Intent**: Plot advancement direction

**Special Cases**:
- **Soliloquy**: `listener_id = null`, `dialogue_direction = "Soliloquy"`
- **Narration**: `speaker_id = "narrator"`, `listener_id = null`
- **Group Dialogue**: Select primary listener as `listener_id`

---

-----------------------------


=== User ===
Shot ID: 

Narrative Intent:


Subject Action:


Entities in this shot: 

**FIRST**: Determine if SILENT (pure action). If SILENT, return empty dialogue, speaker_id "silent".
**IF NOT SILENT**: Search the screenplay excerpt and extract dialogue (who speaks to whom).

SCREENPLAY EXCERPT:


Extract dialogue for this shot. Only dialogue that belongs to THIS shot.
```

## Raw Response

```json
{
  "shot_id": "",
  "full_dialogue": "",
  "speaker_id": "silent",
  "listener_id": "none",
  "is_multi_speaker": false,
  "dialogue_lines": [],
  "sentences": []
}
```
