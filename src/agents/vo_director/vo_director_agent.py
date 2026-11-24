#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
VODirectorAgent — FilmDSL Layer 1 refinement: dialogue + acting direction.

For every shot of a SceneBlueprint:
  1. Dialogue   — if the Story Editor left a shot without a line, re-check the script
                  segment with dialogue_extraction.yaml (who says what to whom) and fill
                  narrative_layer.dialogue; attach the speaker's TTS voice preset.
  2. Performance— infer the performed emotion for this moment (emotion_inference.yaml
                  from line + speaker persona + staging; emotion_visual.yaml on silent
                  shots), tracking the last 3 beats for continuity. This is the paper's
                  Acting Coach; it lands in narrative_layer.performance_emotion/_intensity
                  and flows into the Technical Director's prompts.
  3. Voice design (opt-in) — VoiceDesignAgent writes a fixed TTS voice identity into
                  CharacterAsset.voice_design, so all of a character's lines share one voice.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import SceneBlueprint, ShotBlueprint, DialogueDef
from ...schemas.dialogue import DialogueExtraction, EmotionInference
from ...skills.dialogue_processing import (
    build_character_context,
    build_visual_context,
    fetch_speaker_metadata,
    format_emotion_history,
    get_fallback_emotion,
)

_HERE = Path(__file__).resolve().parent
_NO_SPEAKER = {"", "silent", "none", "environment"}
_GROUP_LISTENERS = {"group", "multiple", "audience"}


class VODirectorAgent:
    """Dialogue supervisor + acting coach (config-driven: dialogue_extraction / emotion_inference / emotion_visual)."""

    def __init__(self):
        self._extractor = ConfigurableAgent(config_path=str(_HERE / "dialogue_extraction.yaml"))
        self._text_emotion = ConfigurableAgent(config_path=str(_HERE / "emotion_inference.yaml"))
        self._visual_emotion = ConfigurableAgent(config_path=str(_HERE / "emotion_visual.yaml"))
        self.emotion_history: List[Dict] = []

    def run_on_blueprint(
        self,
        blueprint: SceneBlueprint,
        script_segment: str,
        asset_library: AssetLibrary,
        *,
        infer_emotion: bool = True,
        design_voices: bool = False,
    ) -> SceneBlueprint:
        """Refine narrative_layer.dialogue (+ performance emotion) on every shot; other layers untouched."""
        print("--- [VODirector] Dialogue + performance direction → narrative_layer ---", flush=True)
        self.emotion_history = []
        self._recovered = set()
        if design_voices:
            self.design_voices(asset_library)
        char_ctx = build_character_context(asset_library)
        for shot in blueprint.shots:
            if shot.narrative_layer is None:
                continue
            self._enrich_dialogue(shot, char_ctx, script_segment, asset_library)
        self._spoken_lines_only(blueprint)
        self._no_repeated_lines(blueprint, script_segment, self._recovered)
        for shot in blueprint.shots:
            if shot.narrative_layer is not None and infer_emotion:
                self._direct_performance(shot, asset_library)
        return blueprint

    @staticmethod
    def _no_repeated_lines(blueprint: SceneBlueprint, script: str, recovered=()) -> None:
        """A line is spoken as many times as the script has it (once, usually). The extractor that recovers lines
        for silent shots re-assigns lines another shot already speaks (LibraryDog: "它替你交罚款？" in shots 08 and
        10); extra copies are removed, recovered ones first. Lines not found in the script are left alone."""
        from collections import Counter
        from ...skills.script_coverage import norm, script_lines
        allowed = Counter(norm(l) for l in script_lines(script))
        groups = {}
        for i, shot in enumerate(blueprint.shots):
            d = shot.narrative_layer.dialogue if shot.narrative_layer else None
            if d and d.has_dialogue and d.text and allowed.get(norm(d.text)):
                groups.setdefault(norm(d.text), []).append((shot.shot_id in recovered, i, shot))
        for key, items in groups.items():
            for _, _, shot in sorted(items)[allowed[key]:]:     # planner's own lines first, then in shot order
                d = shot.narrative_layer.dialogue
                print(f"   ✂️  [{shot.shot_id}] '{d.text}' is already spoken in another shot: now silent", flush=True)
                d.has_dialogue, d.text = False, None

    @staticmethod
    def _spoken_lines_only(blueprint: SceneBlueprint) -> None:
        """Dialogue text is what is said, nothing else: narration around a quote is dropped (spoken_only), and a
        line recovered that way which another shot already speaks as its own line is removed here (the shot stays,
        silent) — otherwise the line is said twice."""
        from ...skills.script_coverage import norm, spoken_only
        clean = {}
        for shot in blueprint.shots:
            d = shot.narrative_layer.dialogue if shot.narrative_layer else None
            if d and d.has_dialogue and d.text and spoken_only(d.text) == d.text:
                clean.setdefault(norm(d.text), shot.shot_id)
        for shot in blueprint.shots:
            d = shot.narrative_layer.dialogue if shot.narrative_layer else None
            if not (d and d.has_dialogue and d.text):
                continue
            said = spoken_only(d.text)
            if said == d.text:
                continue
            other = clean.get(norm(said))
            if other and other != shot.shot_id:
                print(f"   ✂️  [{shot.shot_id}] dialogue was narration + a line {other} already speaks: now silent",
                      flush=True)
                d.has_dialogue, d.text = False, None
            else:
                print(f"   ✂️  [{shot.shot_id}] dialogue narration dropped: {d.text[:40]}… -> {said}", flush=True)
                d.text = said

    # ── 1. dialogue ────────────────────────────────────────────────────────

    def _enrich_dialogue(self, shot: ShotBlueprint, char_ctx: str, script_segment: str, library: AssetLibrary) -> None:
        dialogue = shot.narrative_layer.dialogue

        # The Story Editor already wrote the line: only attach the voice preset.
        if dialogue.has_dialogue and dialogue.text:
            if dialogue.speaker_asset_id and not dialogue.voice_preset:
                dialogue.voice_preset = self._voice_preset(dialogue.speaker_asset_id, library)
            return

        # Marked silent: let the extractor double-check against the script.
        staging = shot.staging_layer
        try:
            extraction: DialogueExtraction = self._extractor.run(
                shot_id=shot.shot_id,
                narrative_action=shot.narrative_layer.narrative_action,
                emotional_beat=shot.narrative_layer.emotional_beat,
                entities=", ".join(e.asset_id for e in staging.entities) if staging else "(unknown)",
                visual_context=build_visual_context(shot),
                character_list=char_ctx,
                script_segment=script_segment,
            )
        except Exception as e:
            print(f"   ⚠️  [{shot.shot_id}] dialogue extraction failed: {e}", flush=True)
            return

        speaker = (extraction.speaker_id or "").strip()
        if not extraction.full_dialogue or speaker in _NO_SPEAKER:
            return
        if speaker == "multiple" and extraction.dialogue_lines:
            speaker = extraction.dialogue_lines[0].speaker_id
        if library.get_character_by_id(speaker) is None:
            print(f"   ⚠️  [{shot.shot_id}] extractor returned unknown speaker {speaker!r}; dialogue kept without speaker", flush=True)
            speaker = None

        listener = (extraction.listener_id or "").strip()
        listener = "group" if listener in _GROUP_LISTENERS else (listener if library.get_character_by_id(listener) else None)

        shot.narrative_layer.dialogue = DialogueDef(
            has_dialogue=True,
            speaker_asset_id=speaker,
            listener_asset_id=listener,
            text=extraction.full_dialogue,
            voice_preset=self._voice_preset(speaker, library),
        )
        self._recovered.add(shot.shot_id)
        print(f"   ✅ [{shot.shot_id}] dialogue recovered: speaker={speaker}, {len(extraction.full_dialogue)} chars", flush=True)

    @staticmethod
    def _voice_preset(speaker_id: Optional[str], library: AssetLibrary) -> Optional[str]:
        char = library.get_character_by_id(speaker_id) if speaker_id else None
        return char.voice_preset_id if char else None

    # ── 2. performance emotion ─────────────────────────────────────────────

    def _direct_performance(self, shot: ShotBlueprint, library: AssetLibrary) -> None:
        n = shot.narrative_layer
        visual = build_visual_context(shot)
        try:
            if n.dialogue.has_dialogue and n.dialogue.text:
                inferred: EmotionInference = self._text_emotion.run(
                    dialogue=n.dialogue.text,
                    visual_context=visual,
                    emotion_history=format_emotion_history(self.emotion_history, last_n=3),
                    **fetch_speaker_metadata(n.dialogue.speaker_asset_id, library),
                )
            else:
                inferred = self._visual_emotion.run(visual_context=visual)
        except Exception as e:
            print(f"   ⚠️  [{shot.shot_id}] emotion inference failed ({e}); rule fallback", flush=True)
            movement = shot.staging_layer.camera.movement if shot.staging_layer else None
            inferred = get_fallback_emotion(n.dialogue.text or "", movement)

        n.performance_emotion = inferred.emotion
        n.performance_intensity = inferred.intensity
        self.emotion_history.append({"shot_id": shot.shot_id, "emotion": inferred.emotion})

    # ── 3. voice design (opt-in) ───────────────────────────────────────────

    def design_voices(self, library: AssetLibrary) -> int:
        """Write a TTS voice identity into every character that has none. Returns how many were designed."""
        from .voice_design import VoiceDesignAgent

        designer = VoiceDesignAgent()
        done = 0
        for char in library.characters:
            if char.voice_design:
                continue
            try:
                char.voice_design = designer.run(char.model_dump(), library.global_style).voice_design
                done += 1
                print(f"   🎙  [{char.id}] voice designed", flush=True)
            except Exception as e:
                print(f"   ⚠️  [{char.id}] voice design failed: {e}", flush=True)
        return done
