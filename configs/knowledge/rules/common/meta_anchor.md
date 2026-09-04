# Meta Info as Constraint Layer (Common)

> **Used by**: StoryEditor, DSLValidator, Cinematographer, VODirector  
> **Token Budget**: ~80 tokens

---

## Mandatory Rules

- **Asset Library is the "Truth Anchor"** — DSL generation and downstream agents MUST comply with it.
- All entity references MUST use Asset IDs (e.g. `char_vito_corleone`), never raw descriptions.
- ProjectSettings constraints MUST be injected into every shot prompt (consistency_constraints field).

## Data Flow

```
Script → Asset Library (meta info) → FilmDSL layers (narrative / staging / render) → video jobs
```
