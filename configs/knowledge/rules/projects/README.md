# Project-level style guide

The Art Department can take a per-project style guide that overrides its default
"derive the style from the script" behaviour — useful when a whole project must
share one look (a series, a stylised adaptation, a genre house style).

## How it is picked up

Put a `style_guide.md` next to the run's `assets/` directory, i.e. in the run root:

```
data/runs/dataset/<Story>/<run_id>/
├── style_guide.md      ← read by ArtDepartmentAgent.run() when present
└── assets/
```

`ArtDepartmentAgent` passes its text to `art_department.yaml` as
`project_style_guide`; the agent then follows it when writing `global_style`,
`narrative_context.global_mood`, colour and character-description emphasis.
There is no global default style file — without a guide the style is inferred
from the script.

## Writing one

Start from [`style_guide_template.md`](style_guide_template.md). Keep it short
and concrete: one global style sentence, the mood vocabulary to use and to avoid,
a colour guide per scene type, and what to emphasise in character descriptions.

After changing a style guide, re-run the Art Department (delete or rename the old
`assets/` folder) — downstream layers inherit the asset library.
