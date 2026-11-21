# Judge / QA calibration set v1 (2026-11-20)

30 shots (LastBus #5, LibraryDog #2, LastBus #4), 3 frames each (`sheet_NN.jpg`), first-pass labels by Claude in
`labels_v1.json` (ok = usable in the film; problem tags: identity / time / text / action). To be spot-checked by the
user. `items.json` holds the system's gate results for the same clips.

Result of v1 (system gates vs labels, 7 unusable shots):
- any visual gate: precision 0.38, recall 0.43
- judge `visual.review`: precision 0.33, recall 0.29 (mostly staging / pedantic constraint flags)
- VLM garbled_text: recall 0.00 (3 shots with legible generated signage missed)
- identity: recall 0.00 (Doudou drawn as a chihuahua in 3 shots: the Art Department wrote "Chihuahua mix" for a
  script "柴犬" — a planning error every later check inherited)

Changes made from it: asset-vs-script fidelity check (art_department/asset_fidelity.yaml), VLM text transcription
gate (`visual.text`), per-character identity against the reference board (`visual.identity`).
Re-score the new gates on this set once the cluster is reachable.


## v2 (2026-11-21): new detectors re-scored on the same 30 shots

| gate set | precision | recall | F1 |
|---|---|---|---|
| v1: judge + VLM flags + continuity | 0.43 | 0.43 | 0.43 |
| v2 all (incl. judge) | 0.44 | 0.57 | 0.50 |
| **v2 specific detectors only (continuity + text + identity)** | **0.80** | **0.57** | **0.67** |
| same, chihuahua shots caught upstream by asset fidelity | 0.75 | 0.75 | 0.75 |

Text gate: VLM transcription; garbled only when prominent AND (VLM says garbled OR adjacent repeated token) — the
VLM alone called "2路 路" not garbled. Bugs found while scoring: VLM answer capped at 300 tokens (the most text-heavy
shot's JSON was cut and silently skipped) and a str.format brace bug that disabled the VLM check; both fixed, and a
crashed check now stops produce.py instead of reading as a pass.
Decision: hard gates = audio.asr, visual.continuity, visual.text, visual.identity (+ film gates); judge and generic
VLM verdicts are advisory.
