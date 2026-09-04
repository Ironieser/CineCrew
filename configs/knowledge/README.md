# Production Rulebook (static knowledge injected into prompts)

Markdown files that agents pull into their prompts through the Jinja globals
`load_knowledge('<path>')` and `load_module_specs('<AgentName>')`
(`src/skills/memory_loader.py`). Setting `DISABLE_KNOWLEDGE=1` turns all of
this off — the "no workflow memory" ablation.

```
rules/common/        shared conventions, composed per agent
  naming.md            asset / shot ID formats
  anti_hallucination.md location & era locks beat training-data priors
  consistency.md       visual + narrative consistency rules
  meta_anchor.md       the Asset Library is the truth anchor
rules/agents/
  dialogue_emotion.md  VO Director dialogue / emotion rules
rules/L2_MODULE_SPECS.md   per-agent working rules; load_module_specs() extracts one section
rules/projects/      how to supply a per-project style guide (+ template)
domain/
  asset_extraction_guide.md  how the Art Department builds the World Bible
errors/
  error_kb.md          known failure modes → rules (repair prompts)
```

## Who injects what

| Agent (YAML) | Files |
|--------------|-------|
| Art Department (`art_department.yaml`) | naming, anti_hallucination, consistency, domain/asset_extraction_guide |
| Story Editor (`story_editor.yaml`) | naming, anti_hallucination |
| Cinematographer (`cinematographer.yaml`) | naming, anti_hallucination |
| DSL Validator (`dsl_validator.yaml`) | naming, meta_anchor, errors/error_kb |
| VO Director (`dialogue_extraction.yaml`) | naming, agents/dialogue_emotion, L2 `VODirectorAgent` section |
| Technical Director (`technical_director.yaml`) | naming, anti_hallucination |

Usage inside a YAML prompt (paths are relative to `configs/knowledge/`):

```yaml
system_prompt_template: |
  ...
  {{ load_knowledge('rules/common/naming.md') }}
  {{ load_module_specs('VODirectorAgent') }}
```

Keep files small (each is ~100-400 tokens) and written for the model, not as a
changelog: state the rule, not the history of how it was found.
