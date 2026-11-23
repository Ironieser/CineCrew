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

### Joint audio-video models (MiniMax H3)

`tools/h3_proxy.py` is such a server for a self-hosted MiniMax H3 (SGLang `/v1/videos`). Per job it rewrites the
shot prompt into H3's structured format with the configured LLM (dialogue as `<d>[Chinese] …</d>`, off-screen lines
as voiceover with closed lips), checks the rewrite deterministically (exact dialogue, no captions clause), copies
reference images to the H3 host, and routes to Ref2VA (character references) or FL2VA (text only).

```bash
python tools/h3_proxy.py            # env: H3_FL2VA_URL, H3_REF2VA_URL, REF_SSH_HOST, REF_REMOTE_DIR, LLM_*
VIDEO_BASE_URL=http://127.0.0.1:30100/v1 VIDEO_MODEL=minimax-h3 \
PIPELINE_SETTINGS=configs/pipeline_settings_h3.yaml python run_dataset_story.py our_dataset/EchoStation
```

`configs/pipeline_settings_h3.yaml` turns on execution with character references instead of T2I keyframes and sets
`production_operator.segment_dialogue: false`, so a dialogue shot is one clip the model voices itself. Every job's
`extra` carries `reference_subjects` (image, name, appearance of each on-screen character) and the `speaker`.
`PIPELINE_SETTINGS=<path>` selects any alternative settings file.

Voice consistency: put a 4-8 s clean `voice.wav` (+ its transcript in `voice.txt`) next to a character's reference
image (`character_list/<Name>/voice.wav`). For a dialogue shot the proxy sends the speaker's voice as `<Audio 1>`
to Ref2VA, so the same character keeps the same timbre across shots. Dialogue shots are lengthened to fit the line
(about 4 Chinese characters per second + 1.8 s).

### QA and post-production

```bash
python tools/qa_report.py <run_dir> --hint "domain words for ASR"     # -> <run>/qa_report.{json,md}
python tools/post_production.py <run_dir>                            # -> <run>/media/film_post.mp4
python tools/qa_report.py <run_dir> --post                           # grade the post-produced film
```

`qa_report` gates each shot on audio (ASR matches the line, no dead air, per-speaker voice similarity, EBU R128
loudness), visuals (VisualJudge score; a VLM checks garbled text, captions, glowing human eyes, missing / extra
people, duplicated one-of-a-kind objects) and pacing (film length vs plan). Failed shots are the `--only` list for
`resume_production`. `post_production` uses the report's speech spans to trim dead air, levels dialogue (-20 LUFS)
and ambience (-30 LUFS) per clip, adds short fades at cuts, burns the dialogue as subtitles while it is spoken, and
normalises the film to -16 LUFS.

### Continuity ledger (ScriptSupervisor)

`script_supervisor` (on in `pipeline_settings_h3.yaml`) writes `narrative_layer.continuity` for every shot: time of
day, weather, lighting, prop holders and wardrobe, plus the changes that happen in the shot. A deterministic pass
keeps time moving forward and props with their holder unless a hand-over is recorded. The entry is appended to each
job prompt (only props held by on-screen characters or changing hands), shown to the VisualJudge, and checked by
`qa_report` (`visual.continuity`: day/night and rain read from frames; a night shot must read as night).

World facts (2–4 per film) are judged describe-then-judge: a blind frame description, then a text-only judge.
Facts about who may be present are written into prompts but not judged there (`judged_facts`): the stranger /
presence detector covers them. With `verify_location_plates: true` the location plates, rendered before the ledger
existed, are judged against the world facts right after this stage; a plate that contradicts them (e.g. a planet
horizon where the story needs a distant globe) is re-rendered with the violation as a correction and the staged
props that have a reference picture (e.g. a code-rendered planet) as conditioning, up to `plate_retries` times. The
new plate goes to the run's `assets/references/`; a supplied plate is never overwritten.

### Hands-off production

`tools/produce.py <story_dir> --hint "..."` runs planning + rendering, then up to `--rounds` QA → regenerate-failed
cycles, post-production and the final QA, and writes `<run>/produce_log.json`. With `generate_references: true` and
`T2I_BASE_URL` pointing at the H3 proxy, character sheets come from `/v1/images/generations` (a 4 s H3 shot; a VLM
picks an upright, eyes-open, front-facing frame, re-rolling if none qualifies). A speaker's voice is cast before
their first line (`<sheet>.voice.wav`) and used as `<Audio 1>` in all of their shots.

### Repair policy (failed shots)

`tools/produce.py` does not re-roll failed shots blindly. `src/skills/repair_policy.py` maps each shot's QA record and
judge checklist to failure types — A identity, B presence, C continuity, D artifact (text / extra objects), E action,
F speech — with the evidence (what the VLM / judge / ASR saw). `configs/repair_policy.yaml` turns type × attempt into
prompt additions (prefix = highest weight), a new seed and a duration change; attempt 2 escalates. A type seen in ≥ 2
shots of a film becomes a story-level lesson appended to later regenerations of that film only (`<run>/memory/`).
Asset-level repair: when one character contradicts its written description (age, gender, species…) in ≥ 2 shots,
the reference sheet itself is wrong — `tools/remake_asset.py` re-renders it with the QA evidence as a correction
(the old sheet is kept as `.bad<N>.png`, the cast voice is dropped and re-cast) and every shot of that character
is re-shot. Sheets are validated against the description (apparent age, gender, outfit); a rejected sheet gets a
random new seed and an LLM rewrite of the appearance text from the rejection reason before it is rendered again.
Dead air alone is never regenerated (post-production trims it); a failure against a stale character expectation is
not regenerated either. `resume_production.py --repair <plan.json>` applies a plan by hand.

### Draft and final tiers

Draft renders use the 8-step turbo LoRA (FP8). Key shots get a final render on replicas served WITHOUT the LoRA at the
full schedule (50 steps; the released weights are CFG-distilled, so a step is one forward): `serve.sh <variant>
<tag> none` on the cluster, then `H3_FINAL_FL2VA_URL` / `H3_FINAL_REF2VA_URL` (and optionally `H3_FINAL_STEPS`) for
the proxy. With those set, `produce.py` re-renders the closing shot and every shot still failing after the repair
rounds at `--tier final`; `resume_production.py --tier final` does it by hand. Expect ~6x the draft time per clip.

### Judge calibration

VisualJudge answers a fixed checklist (`checks`: right_characters, identity_matches, main_action_shown,
integrity_ok, constraints_ok, staging_matches) and sees the characters' reference images after the clip frames.
Acceptance is computed from the hard items; staging (positions, paths, sub-action order) only lowers the score.
When no attempt is accepted the best-scoring one is kept. `tools/rejudge.py <run_dir> --only shot_05` re-judges
every existing attempt of those shots (no generation) and keeps the best: use it after editing `visual_judge.yaml`.

### Resuming production

`tools/resume_production.py <run_dir>` re-runs only the execution stage from a run's saved plan (no LLM planning), with the settings snapshot the run was made with (`<run>/pipeline_settings.yaml`):
`--keep shot_01,shot_02` reuses those clips, `--only shot_05` regenerates just those shots, and
`--resync-characters` re-derives each shot's on-screen characters and reference conditioning
(`technical_director.visible_characters`: template list + staging entities + characters named in the shot's action).


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

