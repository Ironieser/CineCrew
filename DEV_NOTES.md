# Developer Notes

## Crew ↔ code mapping

The paper describes an idealized film crew; the code implements it as
configuration-driven agents. The mapping is not always 1:1 — some crew roles are
performed *within* another agent rather than as a standalone file. This table is
the honest mapping (no agents were invented to match the paper).

| Paper crew role        | Where it lives in code                                   | Notes |
|------------------------|----------------------------------------------------------|-------|
| **Showrunner**         | `art_department/` (`project_settings.yaml`, name "Showrunner") | Global meta + production constraints (`ProjectSettings`). Not a separate agent — produced inside the Art Department package alongside the asset library. |
| **Art Department**     | `art_department/` (`art_department_agent.py` `ArtDepartmentAgent` → `character_prompt.py` `CharacterPromptAgent` → `T2IClient`) | Initializes the `AssetLibrary` from the script (character sheets, sets, props), then generates each character's reference-sheet T2I prompt and image. See "Persona / character initialization" below. |
| **Story Editor**       | `story_editor/` (`story_editor_agent.py` `StoryEditorAgent`) | FilmDSL Layer 1 (narrative actions, emotion beats, dialogue). |
| **Acting Coach**       | `vo_director/` (`emotion_inference.yaml`, `emotion_visual.yaml`) → `narrative_layer.performance_emotion / performance_intensity` | Persona fields (`personality`/`backstory`/`current_motivation`) are initialized by the Art Department; the VO Director turns them + the line + the staging into a per-shot performed emotion (visual-only inference on silent shots), tracking the last 3 beats. Not a standalone agent. |
| **Cinematographer**    | `cinematographer/` (`cinematographer_agent.py`)          | FilmDSL Layer 2 (staging). Name already matched the paper. |
| **Technical Director** | `technical_director/` (`technical_director_agent.py` `TechnicalDirectorAgent`) + `dsl_validator/` | FilmDSL Layer 3 (render spec). `technical_director/visual_prompt_translator.py` resolves `<asset_id>` templates into final prompts. |
| **VO Director**        | `vo_director/` (`vo_director_agent.py` `VODirectorAgent` + `voice_design.py` `VoiceDesignAgent`) | Recovers lines the Story Editor missed (`dialogue_extraction.yaml`), attaches voice presets, runs the Acting Coach above. `design_voices: true` writes a fixed TTS voice identity per character (`CharacterAsset.voice_design`) so every line of that character is voiced consistently. |
| **Production Operator**| `production_operator/` (`production_operator_agent.py` `ProductionOperatorAgent`) + `T2IClient` / `VideoClient` | FilmDSL Layer 4 (assembly) + `VideoJobBatch`; with `execute: true` runs the keyframe → judge → clip → judge loop on the OpenAI-style backends and writes media paths + verdicts back. |
| **Dailies Reviewer**   | `dailies_reviewer/` (`dailies_reviewer_agent.py` `DailiesReviewerAgent` + `visual_judge.py` `VisualJudgeAgent`) | Two gates. (1) Prompt critic: sliding 5-shot window over the resolved T2I/I2V prompts, coarse-to-fine until a pass changes nothing (stage between TechnicalDirector and ProductionOperator). (2) `VisualJudge`: VLM verdict on each rendered keyframe / clip, with a revised prompt on rejection (used inside execution). |
| **Post Supervisor**    | `ProductionOperatorAgent.stitch()` + `src/adapters/media_tools.py` | Cuts the rendered segment clips together in order on the `assembly_layer` transitions (ffmpeg; fade-in on the first shot) → `final_film_path`. The `dialogue_core` job carries the line + `voice_design` + `performance_emotion` for a joint audio-video backend or a TTS stage. |
| **Production Rulebook**| `configs/knowledge/rules/`                                | Static domain priors injected into prompts via `load_knowledge()`. |

### Rename history

Agent classes, package folders, YAML `metadata.name`, `pipeline_settings.yaml` stage
ids, and trace `name:` fields were renamed from the original development
vocabulary to the paper's crew vocabulary:

| Old name              | New name                |
|-----------------------|-------------------------|
| `WorldBuilderAgent` / `world_builder` | `ArtDepartmentAgent` / `art_department` |
| `NarrativeAnalystAgent` / `narrative_analyst` | `StoryEditorAgent` / `story_editor` |
| `DialogueAllocatorAgent` / `dialogue_allocator` | `VODirectorAgent` / `vo_director` |
| `RenderLayerBuilderAgent` / `render_layer_builder` | `TechnicalDirectorAgent` / `technical_director` |
| `WanAdapterAgent` / `wan_adapter` | `ProductionOperatorAgent` / `production_operator` |
| `WanJob` / `WanJobBatch` / `WanClient` | `VideoJob` / `VideoJobBatch` / `VideoClient` (aliases kept in `src/schemas/video_jobs.py`) |

`CinematographerAgent` and `DSLValidatorAgent` kept their names. The artifacts
under `examples/` were produced before the rename and later migrated to the
current names and schemas (trace files, `video_jobs.json`, Layer-0 metadata)
without changing their content.

## Persona / character initialization

Character assets are initialized from the script and then grounded into reference
images — this is what anchors cross-shot identity consistency:

1. **`ArtDepartmentAgent`** (`art_department.yaml`) reads the script and extracts each
   `CharacterAsset`, including the persona fields `personality`, `backstory`, and
   `current_motivation` (alongside appearance / clothing).
2. **`CharacterPromptAgent`** (`character_prompt.yaml`) takes that asset (persona +
   appearance, via `ContextBuilder.character()`) and produces an optimized character
   reference-sheet **T2I prompt** (`SinglePrompt`).
3. **`T2IClient`** generates the character reference image; `ArtDepartmentAgent.update_character_visual()`
   writes its `canonical_image_path` into the asset's `visual_references`.

Downstream, the Technical Director attaches those sheets to every keyframe of the
character (`conditioning.character_consistency`, rendered as TI2I "Picture N"
prompts through `images.edit`), and the VO Director reuses the persona fields for
performance emotion.

> `run_dataset_story.py` first *links* pre-supplied images
> (`our_dataset/<Story>/character_list/<Name>/best.png`, `link_character_images`) and
> then, with `art_department.generate_references: true`, calls
> `ArtDepartmentAgent.generate_references()` for every character still without a sheet
> and for every location (establishing shot), so the chain project meta → constraints →
> text assets → reference images is closed before Layer 1 starts.

## Architecture in one paragraph

Every agent is the same generic `ConfigurableAgent` (`src/engine/base_agent.py`)
driven by a YAML file (prompts + an `output_schema` dotted path to a Pydantic
model). `ConfigurableAgent.run(**kwargs)` renders Jinja2 prompts (with
`load_knowledge()` pulling in the Production Rulebook), asks the LLM for
structured JSON via `instructor`, and writes a markdown trace log. To change an
agent's behavior, edit its YAML — not Python. Each agent is its own package
`src/agents/<name>/` holding `<name>_agent.py` plus its co-located YAML config(s);
the class picks its YAML (an absolute path from the package dir), supplies kwargs,
and post-processes the structured result. `src/pipeline.py` reads the enabled
stages from `configs/pipeline_settings.yaml` and threads one `SceneBlueprint`
(FilmDSL) through every enabled stage in order.

## Model backends

All model access goes through the OpenAI API shape (`src/config.py`):

- **LLM** — `src/utils/get_llm_client()` builds an `openai.OpenAI` (or
  `AzureOpenAI` when `LLM_PROVIDER=azure`) wrapped by `instructor` in JSON mode.
- **T2I** — `src/adapters/t2i_client.py` → `images.generate` (T2I) / `images.edit` (TI2I with reference sheets).
- **Video** — `src/adapters/video_client.py` → `videos.create` / `retrieve` /
  `download_content` (+ `variant="spritesheet"` or ffmpeg for judge frames).
  Non-OpenAI knobs travel in `extra_body`.
- **VLM judge** — same LLM client; `ConfigurableAgent.run(images=[...])` sends
  image parts in the user turn.

Because of that, "adding a new T2V model" means running (or writing) an
OpenAI-compatible server for it — the framework does not change.

## Ablation cascade

Because each stage writes exactly one FilmDSL layer that the next stage reads, the
pipeline is a clean cascade — so ablations are config/env changes, no code edits:

| Ablation axis                | How to toggle |
|------------------------------|---------------|
| Remove an agent / stage      | `enabled: false` (or delete the entry) for that stage in `configs/pipeline_settings.yaml` |
| Closed-loop critic (Dailies) | drop `dailies_reviewer` → "ours without critic"; keep it → "ours + critic" |
| DSL validation               | drop `dsl_validator` |
| Workflow memory (rules)      | env `DISABLE_KNOWLEDGE=1` → `load_knowledge()` / `load_module_specs()` inject nothing |
| Asset (reference-image) memory | skip `link_character_images()` in the entry script |
| Refinement depth             | `dailies_reviewer.max_rounds` |
| Acting Coach                 | `vo_director.infer_emotion: false` |
| Visual judge at execution    | `production_operator.judge: false` (render once, no retries) |

The no-DSL baseline (a flat DirectPrompt instead of the layered Blueprint) is a
separate *baseline* path, not part of this "ours"-only release; the
`src/schemas/direct_prompt.py` schema is retained for reference.

## Provenance

This repository is the cleaned, public "ours" code for the paper. Legacy and
experimental paths from development (the baseline package, anime-style
agents/configs, one-off experiment scripts) were dropped. The closed-loop critic
was kept and ships as the `DailiesReviewer` stage. The single shipped entry point
is `run_dataset_story.py`.
