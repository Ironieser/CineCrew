# Known Failure Modes (injected into repair prompts)

> **Purpose**: the recurring ways LLM output has violated the FilmDSL contract, and the rule that prevents each.  
> **Used by**: DSLValidator (repair step). ~400 tokens.

| # | Failure | Rule |
|---|---------|------|
| E1 | Invented enum value (e.g. `importance: "symbolic"`) | Use ONLY the values listed for the field: `importance` ∈ critical / supporting / background; `type` ∈ INT / EXT / UNKNOWN; `shot_scale` ∈ ECU / CU / MCU / MS / MLS / LS / ELS / OTS / POV. |
| E2 | `null` in a required field, or a value in a field that should be `null` | Optional fields (`voice_preset_id`, `speaker_asset_id` on silent shots, `environment_id` when unknown) may be null; required text fields never are. |
| E3 | Reference to an Asset ID that is not in the library (`char_luca_brasi` when only `char_vito` exists) | Every `asset_id`, `environment_id`, `speaker_asset_id`, `listener_asset_id` MUST be copied verbatim from the Asset Library. Never derive, pluralise, re-case or invent IDs. If a character truly is not in the library, leave them out. |
| E4 | Location listed as an entity, or a character as `environment_id` | `environment_id` takes `loc_*` only; `entities[].asset_id` takes `char_*` / `prop_*` only. |
| E5 | Shot too short (< 1 s) or absurdly long (> 60 s) | Keep `duration_seconds` between 1 and 60; split long beats into several shots. |
| E6 | Multi-speaker exchange attributed to one speaker | When several characters speak in one shot, `is_multi_speaker = true` and every line goes into `dialogue_lines` with its own `speaker_id` / `listener_id`. |
| E7 | Dialogue translated or paraphrased | Dialogue text stays verbatim and in the script's language; agents may segment and annotate it, never rewrite it. |
| E8 | Truncated JSON on long inputs | Output the complete object; prefer fewer, well-formed shots over an unfinished list. |
