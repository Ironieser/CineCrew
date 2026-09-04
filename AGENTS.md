# CineCrew — guide for coding agents

This file is for AI coding assistants (Claude Code, Cursor, Copilot, Codex, …)
and for humans who want the 5-minute mental model. `CLAUDE.md` just points here.

## What this repo is

A multi-agent pipeline that compiles a written narrative into **FilmDSL** — a
single layered JSON document (`SceneBlueprint`) — and then into executable
text-to-image / text-to-video job specs. It is the public code for
*Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation* (ECCV 2026).

Key idea: the script is first distilled into an **Asset Library** (characters,
locations, props with stable IDs) plus global production constraints; every later
stage must reference those IDs. That's what keeps long videos consistent.

## Run / test

```bash
pip install -r requirements.txt
cp .env.example .env                         # put LLM_API_KEY in it
python run_dataset_story.py our_dataset/BetterCallSaul2
```

- Needs a real LLM key; the run costs tokens (~10–15 LLM calls per story).
- Outputs go to `data/runs/dataset/<story>/<run_id>/` (gitignored).
- There is no test suite. The cheap sanity checks are:
  - `python -c "import src.pipeline, src.adapters"` (imports + config load)
  - Build jobs offline from a shipped example (no LLM):
    ```python
    from src.schemas.blueprint import SceneBlueprint; from src.schemas.assets import AssetLibrary
    from src.agents.production_operator import ProductionOperatorAgent
    ex = "examples/BetterCallSaul2/2026-03-05_07-58-36"
    bp = SceneBlueprint.model_validate_json(open(f"{ex}/shots/scene_blueprint_final.json").read())
    lib = AssetLibrary.model_validate_json(open(f"{ex}/assets/asset_library.json").read())
    ProductionOperatorAgent().build_from_blueprint(bp, lib)
    ```
- `examples/` has full artifacts (assets, blueprints, per-agent trace logs) for 13
  stories — read those to see what each agent is supposed to produce.

## How the code is organized

```
run_dataset_story.py          entry point: load story → ArtDepartment → link images → run_pipeline()
src/pipeline.py               stage runner; one SceneBlueprint threaded through the enabled stages
src/engine/base_agent.py      ConfigurableAgent: YAML prompts (Jinja2) + Pydantic output schema → instructor call
src/agents/<crew>/            one package per crew member:
                                <crew>_agent.py   thin controller (builds kwargs, post-processes)
                                <crew>.yaml       the prompts + output_schema (THIS is where behavior lives)
                              dailies_reviewer/ also holds visual_judge.{py,yaml} (VLM gate on rendered media)
src/schemas/                  Pydantic models. blueprint.py = FilmDSL; assets.py = AssetLibrary;
                              video_jobs.py = VideoJob/VideoJobBatch; critic.py = ShotCriticResult/VisualReview
src/adapters/                 OpenAI-SDK clients: t2i_client.py (images.generate / images.edit),
                              video_client.py (videos.create / retrieve / download_content);
                              media_tools.py = local ffmpeg helpers (frame sampling, clip concat)
src/skills/                   deterministic helpers (context builders, asset I/O, DSL validation, knowledge loader)
src/utils/                    LLM client factory, trace logging, truncation limits
src/config.py                 env-only settings (.env auto-loaded). No secrets in code.
configs/pipeline_settings.yaml  stage order / enable flags / per-stage options / limits
configs/knowledge/            "Production Rulebook" injected into prompts via {{ load_knowledge(...) }}
```

Pipeline order (each stage writes exactly one layer the next one reads):

```
art_department → story_editor → cinematographer → dsl_validator → vo_director
→ technical_director → dailies_reviewer (critic loop) → production_operator
```

| Stage | Writes |
|-------|--------|
| art_department | `AssetLibrary` (+ `ProjectSettings`), Layer-0 `metadata` (render target from `VIDEO_SIZE`/`VIDEO_FPS`), `global_style`; `generate_references: true` → reference sheets / establishing shots |
| story_editor | `shots[].narrative_layer` (L1) |
| cinematographer | `shots[].staging_layer` (L2) |
| dsl_validator | validates/corrects entity IDs in L2 |
| vo_director | `narrative_layer.dialogue` (recovered lines, voice preset) + `performance_emotion/_intensity` |
| technical_director | `shots[].render_layer` (L3; resolved T2I / TI2I / I2V prompts + reference conditioning) |
| dailies_reviewer | rewrites weak resolved prompts, 5-shot window, until convergence |
| production_operator | `shots[].assembly_layer` (L4) + `VideoJobBatch`; `execute: true` → keyframe → VisualJudge → clip → VisualJudge → stitch (ffmpeg), results written back |

## Conventions that matter

- **Prompt changes go in YAML, not Python.** Each `src/agents/<crew>/*.yaml` has
  `system_prompt_template`, `user_prompt_template`, `output_schema` (dotted path to
  a Pydantic class). `ConfigurableAgent` refuses relative config paths — agents pass
  `str(Path(__file__).parent / "x.yaml")`.
- **Structured output only.** Every LLM call returns a validated Pydantic model via
  `instructor` (JSON mode). Don't parse free text.
- **Asset IDs are the contract.** Prompts use `<char_x>` / `<loc_y>` / `<prop_z>`
  placeholders that `visual_prompt_translator` resolves. Never invent an ID that is
  not in the `AssetLibrary`; `dsl_validator` will strip or correct it.
- **Backends are OpenAI-shaped.** LLM → `/chat/completions`; T2I → `/images/generations`;
  video → `/videos` (+ `retrieve`, `download_content`). Configure with
  `LLM_*` / `T2I_*` / `VIDEO_*` env vars. To support a new T2V model, run it behind an
  OpenAI-compatible server — do not add model-specific code to the pipeline. Extra
  model knobs go through `extra_body` / `VideoJob.extra`.
- **Every agent call is traced** to `<run>/logs/<Agent>_span_NNNN.md` (prompt,
  raw JSON, timing, tokens). Read these first when debugging an agent.
- **Vision calls** go through the same `ConfigurableAgent.run(images=[...])`; the
  user turn becomes text + `image_url` data URIs. Only `VisualJudgeAgent` uses it.
- **Execution is opt-in and separate from planning** (`production_operator.execute`).
  Planning must never require a T2I/T2V backend; `build_from_blueprint()` makes no
  network calls. Media and verdicts are written back into the blueprint, and the
  final rendered prompt replaces the planned one so the blueprint stays truthful.
- **Audio rides on the FilmDSL, not on ad-hoc code.** Dialogue segmentation
  (`prelude / dialogue_core / afterglow`), `voice_design`, `performance_emotion`,
  `assembly_layer.audio_tracks` and `lip_sync_constraint` are the contract for a TTS
  stage or a joint audio-video model. Extend those fields rather than adding side channels.
- **Truncation happens in exactly two places** (`configs/pipeline_settings.yaml → limits`):
  the script fed to Art Department and the `script_segment` used by the DSL stages.
- **Ablations are config toggles** (`enabled: false`, `DISABLE_KNOWLEDGE=1`), never
  code branches. Keep it that way.
- Legacy names `WanJob` / `WanJobBatch` are aliases of `VideoJob` / `VideoJobBatch`.
- The rulebook under `configs/knowledge/` is written *for the model*: rules only,
  no changelog / error history. Keep it that way when adding files.

## When editing

- Header comment block on every `.py` (project / paper / license) — keep it on new files.
- Keep `src/pipeline.py` stage handlers small; put logic in the agent package.
- New stage = new package under `src/agents/`, a handler branch in `pipeline.py`,
  and an entry in `configs/pipeline_settings.yaml`. Update `docs/USAGE.md` and the crew
  map in `DEV_NOTES.md` (the README stays at the paper's level of description).
- Don't commit anything under `data/`, `.env`, or media (`.mp4`, `.png` outside
  `docs/` and `our_dataset/`) — see `.gitignore`.
- No secrets, absolute local paths, or hostnames in code, configs, or examples.
