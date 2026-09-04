# Asset Extraction Guide (ArtDepartment)

> **Purpose**: How to extract the World Bible (Asset Library) from a script excerpt.  
> **Used by**: ArtDepartment Agent (src/agents/art_department/art_department.yaml)

---

## Extraction Rules

1. **Characters**: From scene headings and dialogue (e.g. `BONASERA:`, `DON CORLEONE:`).  
   - ID: `char_{snake_case_name}` (e.g. `char_bonasera`, `char_don_corleone`).  
   - Include: `description` (physical), `voice_description`, `personality`, `backstory`, `current_motivation` for this scene.

2. **Locations**: From scene headings (e.g. `INT. DON'S OFFICE - NIGHT`).  
   - ID: `loc_int_{name}` or `loc_ext_{name}`.  
   - `type`: STRICTLY `INT`, `EXT`, or `UNKNOWN`.  
   - `visual_style`: Lighting, atmosphere, key visual elements.

3. **Props**: Objects that matter to the scene (desk, blinds, chair, etc.).  
   - ID: `prop_{name}`.  
   - `importance`: `critical` | `supporting` | `background`.

4. **Narrative Context**: `time_period`, `global_mood`, `key_events` (list), `cultural_context` from the script.

5. **Constraints**: Keep `description` ≤ 50 words, `personality` ≤ 30 words, `visual_style` ≤ 40 words.

---

## Anti-Hallucination

- Do **not** invent characters/locations/props not present in the excerpt.  
- Use **ProjectSettings** (location_lock, era_lock, negative_constraints) when the script implies a known setting (e.g. "The Godfather" → Long Island, 1945, NOT Italy).
