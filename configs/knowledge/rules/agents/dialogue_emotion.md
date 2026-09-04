# Dialogue & Emotion Rules (VO Director)

> **Used by**: dialogue_extraction.yaml (and, by reference, the emotion agents)  
> **Token Budget**: ~150 tokens

---

## Dialogue

- **Speaking shots** MUST carry `text`, `speaker_asset_id` (a `char_*` ID) and, when known, the speaker's `voice_preset`.
- **Multi-speaker** shots MUST identify the speaker of every line (`dialogue_lines`).
- **Silent shots** are marked explicitly (`speaker_id = "silent"`); do not invent lines to fill a shot.

## Emotion

- Every shot gets a performed emotion — from the line + speaker persona when there is dialogue, from the visuals alone when there is not.
- **Continuity**: consider the previous 3 beats; changes must be logical (grief → desperation → anger), never abrupt.
- Distinguish character emotion from environmental atmosphere.

## Language

- Dialogue text stays **verbatim and in the script's language** (Chinese scripts keep Chinese lines). Agents segment, attribute and annotate lines; they never translate or rewrite them.
