# Skill-layer prompt templates

`skill_templates.yaml` holds the Jinja2 templates rendered by
`src/skills/prompt_building.py`. They are **not** agent prompts (those live next
to each agent in `src/agents/<crew>/*.yaml`); they build the *input text* handed
to a prompt-writing sub-agent, or a pure-template prompt when no LLM is used.

| Key | Rendered by | Used for |
|-----|-------------|----------|
| `character_request` | `ContextBuilder.character()` | input to `CharacterPromptAgent` (character reference-sheet T2I prompt) |
| `character_visual` | `FallbackGenerator.character_visual()` | template-only character sheet prompt (`ArtDepartmentAgent.update_character_visual`) |
| `location_visual` | `FallbackGenerator.location_visual()` | template-only location establishing-shot prompt |
| `prop_visual` | `FallbackGenerator.prop_visual()` | template-only prop reference prompt |

Placeholders match the `ctx` dict each function builds; edit the wording here
without touching Python. A missing key falls back to the default string in
`prompt_building.py`.
