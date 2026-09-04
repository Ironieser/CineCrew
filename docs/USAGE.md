# CineCrew — usage guide

Installation is in the [README](../README.md#-installation--usage); this page covers configuration, running, outputs, execution with the visual judge, swapping backends, examples, ablations, and the repository layout.

## Configuration

Everything is configured through environment variables (a `.env` file at the
project root is loaded automatically; see [`.env.example`](../.env.example)). No
secrets are ever stored in the repo.

All three model roles speak the **OpenAI API shape**, so OpenAI, Azure OpenAI,
vLLM, Ollama, LiteLLM, or a self-hosted wrapper are interchangeable — point the
`*_BASE_URL` at the server and name the `*_MODEL` it serves.

| Role | Endpoint used | Variables | Default |
|------|---------------|-----------|---------|
| **LLM** (the crew) | `POST {LLM_BASE_URL}/chat/completions` | `LLM_API_KEY` (required), `LLM_BASE_URL`, `LLM_MODEL`, `LLM_PROVIDER` (`openai` \| `azure`), `AZURE_API_VERSION` | `api.openai.com`, `gpt-5` |
| **T2I** (keyframes, reference sheets) | `POST {T2I_BASE_URL}/images/generations` (+ `/images/edits`) | `T2I_MODEL`, `T2I_BASE_URL`, `T2I_API_KEY`, `T2I_SIZE`, `T2I_KEYFRAME_SIZE` | self-hosted **Qwen-Image**: `qwen-image` @ `http://localhost:8000/v1` |
| **Video** (T2V / I2V) | `POST {VIDEO_BASE_URL}/videos` + poll / download | `VIDEO_MODEL`, `VIDEO_BASE_URL`, `VIDEO_API_KEY`, `VIDEO_SIZE`, `VIDEO_FPS`, `VIDEO_TIMEOUT` | self-hosted **Wan 2.2**: `wan22-t2v` @ `http://localhost:8090/v1` |

The paper's results use Qwen-Image (T2I) and Wan 2.2 (T2V / I2V), which is why
they are the defaults; `T2I_API_KEY` / `VIDEO_API_KEY` fall back to `LLM_API_KEY`.
Swapping in OpenAI's `gpt-image-1` / `sora-2` or any other model is just a
different `*_MODEL` + `*_BASE_URL`.

Other switches: `LLM_MAX_RETRIES` (default `2`; `0` = fail-fast), `LLM_TIMEOUT`
(seconds per request, default `600`), `LLM_MAX_COMPLETION_TOKENS` (default `32768`),
`TRACE_LOGS=0` (disable per-agent trace logs), `DISABLE_KNOWLEDGE=1` (ablation: no
Production Rulebook injection).

<details>
<summary><b>Example <code>.env</code> files</b> (OpenAI · Azure OpenAI · local vLLM / Ollama)</summary>

```ini
# OpenAI
LLM_API_KEY=sk-...
LLM_MODEL=gpt-5
```

```ini
# Azure OpenAI
LLM_PROVIDER=azure
LLM_API_KEY=...
LLM_BASE_URL=https://<resource>.openai.azure.com
LLM_MODEL=<deployment-name>
AZURE_API_VERSION=2024-10-21
```

```ini
# Local OpenAI-compatible server (vLLM, Ollama, ...)
LLM_API_KEY=EMPTY
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=Qwen/Qwen3-235B-A22B
```

</details>


## Running the pipeline

```bash
python run_dataset_story.py <story_dir>                       # a story directory
python run_dataset_story.py <collection>.json --moment <id>   # one scene of a moments collection
python run_dataset_story.py <story_dir> --skip dailies_reviewer   # turn any stage off from the CLI
python run_dataset_story.py <story_dir> --execute             # also render, judge and cut the film
```

A story directory contains a script and, optionally, one reference image per
character — characters without one (and all locations) get a rendered reference
when `art_department.generate_references: true`:

```
our_dataset/<Story>/
├── script_synopsis.json             { "MovieScript": "...", "Character": ["Saul", "Judge"] }
└── character_list/<Name>/best.png   reference image (linked to the matching character asset)
```

Which stages run, and in what order, is `configs/pipeline_settings.yaml`
(`pipeline.stages`). Every stage is a one-line `enabled: false` away from being
skipped, which is also how the ablations are run.

Programmatic use:

```python
from src.pipeline import run_pipeline
ctx = run_pipeline(open("script.txt").read(), run_root="data/runs/my_story")
blueprint  = ctx["scene_blueprint"]   # FilmDSL (SceneBlueprint)
video_jobs = ctx["video_jobs"]        # VideoJobBatch
```


## Outputs

```
data/runs/dataset/<story>/<run_id>/
├── assets/   asset_library.json, project_settings.json, characters/, locations/, props/
├── shots/    scene_blueprint_final.json   ← FilmDSL, all four layers
│             video_jobs.json              ← VideoJobBatch: executable T2V/I2V job specs
│             validation_report.json       ← asset-ID checks + repairs made by the DSL validator
│             dailies_report.json          ← what the prompt critic changed
│             video_results.json           ← only when execute: true
├── media/    keyframes/, clips/, frames/, film.mp4  ← only when execute: true
└── logs/     one markdown trace per agent call + index.md
```


## Execution and VLM review

The blueprint is a complete plan; turning it into pixels is a separate, opt-in
step so that planning stays cheap and backend-agnostic. With
`production_operator.execute: true` (or `--execute`) the Production Operator runs
a ReAct loop per shot:

```
keyframe  = T2I / TI2I(resolved prompt [+ character reference sheets])  ─┐
            VisualJudge (VLM) → accepted?  else retry with its revised prompt ┘  ≤ max_retries
clip      = I2V(keyframe, resolved_i2v)                                    ─┐
            sample frames → VisualJudge → accepted?  else retry              ┘  ≤ max_retries
```

`VisualJudge` (`src/agents/dailies_reviewer/visual_judge.yaml`) is the second half
of the Dailies Reviewer: the first half critiques the *prompts* before rendering,
this one looks at the *result* — subject count and identity against the
appearance sheets, action and framing, artifacts, hard constraints — and, when it
rejects, returns a complete corrected prompt for the next attempt. Verdicts,
attempt logs, keyframe and clip paths, and the prompt that finally rendered are
all written back into the blueprint (`render_layer.visual_review`,
`keyframe_image_path`, `video_clip_paths`).

Finally the clips are cut together in shot order (`ffmpeg`, fade-in on the first
shot as recorded in `assembly_layer`) into `<run>/media/film.mp4`
(`blueprint.final_film_path`).

Options on the stage: `judge` (default `true`), `max_retries` (default `1`),
`keyframes` (default `true`; `false` skips keyframes and conditions I2V on the
reference sheets), `stitch` (default `true`). Frames for the video judge come from
the backend's spritesheet (`/videos/{id}/content?variant=spritesheet`) or, failing
that, `ffmpeg`. Shot keyframes are rendered at `T2I_KEYFRAME_SIZE` (defaults to
`VIDEO_SIZE`); OpenAI's `gpt-image-1` needs `1536x1024` there, and Sora accepts
only 4 / 8 / 12-second clips, to which segment durations are snapped automatically.

The judge uses the same `LLM_*` model, which therefore needs vision input
(GPT-5 / GPT-4o class, or a vision-capable open model behind your endpoint).

**Dialogue and audio.** Spoken shots are cut into `prelude / dialogue_core /
afterglow` segments so a line can be aligned to its clip, the VO Director gives
every character a fixed voice identity (`voice_design`, `vo_director.design_voices`)
and every shot a performed emotion, and `assembly_layer` carries the dialogue /
BGM tracks with `lip_sync_constraint` on speaking clips. The `dialogue_core` job
carries the line, the speaker's voice and those instructions, so a joint
audio-video model behind `VIDEO_BASE_URL` voices it directly; a TTS stage consumes
the same fields.


## Bring your own T2V / T2I model

The framework never talks to a specific model. `src/adapters/` holds two thin
clients built on the official `openai` SDK:

- `T2IClient` → `images.generate(model, prompt, size, extra_body={negative_prompt, steps, cfg, seed})`,
  or `images.edit(image=[reference sheets], ...)` for reference-conditioned keyframes
- `VideoClient` → `videos.create(model, prompt, size, seconds, input_reference, extra_body={...})`,
  then `videos.retrieve` until `completed`, then `videos.download_content`.

Anything that is not part of the OpenAI schema (negative prompt, fps, frame
count, seed, the dialogue payload, or your own knobs via `VideoJob.extra`) is sent
in the request body, where a self-hosted server can read it and a strict OpenAI
endpoint ignores it. So to run Wan 2.2 (the default), LTX-Video, CogVideoX,
HunyuanVideo, Sora, … you only need a server that exposes those three `/videos`
routes (and/or `/images/generations` for T2I) — then set `VIDEO_BASE_URL`,
`VIDEO_MODEL`, and `VIDEO_API_KEY`. The FilmDSL, the crew, and the job batch stay
exactly the same.


## Examples

`examples/<story>/<run_id>/` ships the artifacts of 13 narratives — each
directory is one run of `run_dataset_story.py` — so you can inspect what each crew
member produced without spending tokens:

```
assets/asset_library.json        the Asset Library (characters, locations, props, constraints)
shots/scene_blueprint_final.json the FilmDSL, all four layers
shots/video_jobs.json            the VideoJobBatch
logs/                            one trace per agent call (rendered prompt, raw JSON, tokens) + index.md
```

Media is not included; paths inside the files are relative to the repo root.


## Ablations

The cascade is config-driven, so the paper's ablations are toggles, not code:

| Axis | Toggle |
|------|--------|
| Remove an agent / stage | `enabled: false` in `configs/pipeline_settings.yaml` (or `--skip <stage>`) |
| Closed-loop critic | drop `dailies_reviewer` (→ "ours w/o critic") |
| DSL validation | drop `dsl_validator` |
| Workflow memory (rulebook) | `DISABLE_KNOWLEDGE=1` |
| Asset (reference-image) memory | skip `link_character_images()` in the entry script |
| Refinement depth | `dailies_reviewer.max_rounds` |
| Acting Coach | `vo_director.infer_emotion: false` |
| Visual judge at execution | `production_operator.judge: false` |


## Repository layout

```
run_dataset_story.py       entry point
src/
├── config.py              env-driven settings (LLM / T2I / VIDEO), loads .env
├── pipeline.py            config-driven stage runner; threads one SceneBlueprint through the crew
├── engine/base_agent.py   ConfigurableAgent — YAML prompts + Pydantic schema → structured LLM call
├── agents/<crew>/         one package per crew member: <crew>_agent.py + its YAML prompt(s)
├── schemas/               FilmDSL (blueprint.py), assets.py, video_jobs.py, critic.py, ...
├── adapters/              OpenAI-style clients: t2i_client.py, video_client.py; ffmpeg helpers
├── skills/                deterministic helpers: context building, asset I/O, validation
└── utils/                 LLM client, tracing, limits
configs/
├── pipeline_settings.yaml stage list, ablation toggles, truncation limits
├── knowledge/             the Production Rulebook (rules/, domain/, errors/)
└── prompts/               Jinja2 templates used by the skill layer
our_dataset/               bundled scripts + character reference images
examples/                  artifacts of 13 example runs
docs/website/              project page (GitHub Pages)
```


## Project page

The page lives in [`docs/website/`](website/) and is published by
[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) to GitHub Pages on
every push that touches it (repository *Settings → Pages → Source: GitHub Actions*).
The demo videos are served from the
[`website-media`](https://github.com/Ironieser/CineCrew/releases/tag/website-media)
release so the source tree stays small; to preview locally, run
`python -m http.server -d docs/website` and open `http://localhost:8000`.

