# Naming Conventions (Common)

> **Used by**: ArtDepartment, StoryEditor, DSLValidator, Cinematographer, VODirector  
> **Token Budget**: ~150 tokens

---

## Asset ID Format

- **Characters**: `char_{lowercase_name}` Example: `char_vito_corleone`
- **Locations**: `loc_{type}_{name}` Example: `loc_int_dons_office`
- **Props**: `prop_{name}` Example: `prop_cat`
- **Voices**: `voice_{character_name}` Example: `voice_bonasera`

## Shot ID Format

- **Original Shots**: `shot_{number}_{brief_description}` Example: `shot_01_vito_listens`
- **Clip segments** (code-generated, not by the LLM): `{shot_id}_{prelude|dialogue_core|afterglow|single}`

## Multimodal Storage (Reference)

- **Reference images**: `CharacterAsset.visual_references.canonical_image_path`
- **Voice samples**: `CharacterAsset.audio_references.voice_sample_path`

**Mandatory**: All entity references MUST use Asset IDs (e.g. `char_vito_corleone`), never raw descriptions. Do NOT generate non-existent Asset IDs.
