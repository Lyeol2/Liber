from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


HORMONE_DOPAMINE = "dopamine"
HORMONE_SEROTONIN = "serotonin"
HORMONE_OXYTOCIN = "oxytocin"
HORMONE_ENDORPHIN = "endorphin"
HORMONE_CORTISOL = "cortisol"
HORMONE_ADRENALINE = "adrenaline"
HORMONE_NORADRENALINE = "noradrenaline"

HORMONES = (
    HORMONE_DOPAMINE,
    HORMONE_SEROTONIN,
    HORMONE_OXYTOCIN,
    HORMONE_ENDORPHIN,
    HORMONE_CORTISOL,
    HORMONE_ADRENALINE,
    HORMONE_NORADRENALINE,
)

MIN_HORMONE_LEVEL = 0.0
MAX_HORMONE_LEVEL = 1.0

DEFAULT_DOPAMINE = 0.50
DEFAULT_SEROTONIN = 0.55
DEFAULT_OXYTOCIN = 0.45
DEFAULT_ENDORPHIN = 0.40
DEFAULT_CORTISOL = 0.25
DEFAULT_ADRENALINE = 0.20
DEFAULT_NORADRENALINE = 0.30

DEFAULT_RECOVERY_RATE = 0.08
DEFAULT_INTERACTION_RATE = 0.05
DEFAULT_TIME_SCALE = 1.0
MIN_TIME_SCALE = 0.0

DEFAULT_BASELINE = {
    HORMONE_DOPAMINE: DEFAULT_DOPAMINE,
    HORMONE_SEROTONIN: DEFAULT_SEROTONIN,
    HORMONE_OXYTOCIN: DEFAULT_OXYTOCIN,
    HORMONE_ENDORPHIN: DEFAULT_ENDORPHIN,
    HORMONE_CORTISOL: DEFAULT_CORTISOL,
    HORMONE_ADRENALINE: DEFAULT_ADRENALINE,
    HORMONE_NORADRENALINE: DEFAULT_NORADRENALINE,
}

# This is a normalized character/cognitive state model, not a medical model.
# Serotonin is associated with emotional stability, impulse control, and threat
# dampening, so it reduces stress-axis and sympathetic arousal signals.
# Cortisol models stress-axis activation: it suppresses reward sensitivity,
# stability, social bonding, and comfort while raising arousal signals.
# Dopamine supports exploration and action initiation; it can lift alertness
# while weakly competing with calm satisfaction.
# Oxytocin models social safety and bonding, raising stable comfort signals and
# buffering stress and defensive arousal.
# Endorphin models endogenous analgesia and comfort, supporting reward and mood
# stability while lowering stress burden.
# Adrenaline models acute action readiness, raising stress and alertness while
# disrupting calm stability.
# Noradrenaline models attention and vigilance, supporting action readiness while
# weakly pushing against calm satisfaction.
DEFAULT_INTERACTION_MATRIX = {
    HORMONE_DOPAMINE: {
        HORMONE_SEROTONIN: -0.10,
        HORMONE_NORADRENALINE: 0.20,
    },
    HORMONE_SEROTONIN: {
        HORMONE_CORTISOL: -0.35,
        HORMONE_ADRENALINE: -0.25,
        HORMONE_NORADRENALINE: -0.15,
    },
    HORMONE_OXYTOCIN: {
        HORMONE_SEROTONIN: 0.25,
        HORMONE_ENDORPHIN: 0.20,
        HORMONE_CORTISOL: -0.35,
        HORMONE_ADRENALINE: -0.20,
    },
    HORMONE_ENDORPHIN: {
        HORMONE_DOPAMINE: 0.15,
        HORMONE_SEROTONIN: 0.15,
        HORMONE_CORTISOL: -0.25,
    },
    HORMONE_CORTISOL: {
        HORMONE_DOPAMINE: -0.25,
        HORMONE_SEROTONIN: -0.30,
        HORMONE_OXYTOCIN: -0.25,
        HORMONE_ENDORPHIN: -0.20,
        HORMONE_ADRENALINE: 0.30,
        HORMONE_NORADRENALINE: 0.25,
    },
    HORMONE_ADRENALINE: {
        HORMONE_SEROTONIN: -0.20,
        HORMONE_CORTISOL: 0.20,
        HORMONE_NORADRENALINE: 0.30,
    },
    HORMONE_NORADRENALINE: {
        HORMONE_DOPAMINE: 0.15,
        HORMONE_SEROTONIN: -0.15,
        HORMONE_ADRENALINE: 0.20,
    },
}


def _clamp_level(value: float) -> float:
    return max(MIN_HORMONE_LEVEL, min(MAX_HORMONE_LEVEL, float(value)))


def _copy_hormone_map(source: Mapping[str, float]) -> dict[str, float]:
    return {hormone: _clamp_level(source[hormone]) for hormone in HORMONES}


def _copy_interaction_matrix(
    source: Mapping[str, Mapping[str, float]]
) -> dict[str, dict[str, float]]:
    return {
        source_hormone: dict(targets)
        for source_hormone, targets in source.items()
    }


@dataclass
class HormoneBody:
    levels: dict[str, float] = field(
        default_factory=lambda: _copy_hormone_map(DEFAULT_BASELINE)
    )
    baseline: dict[str, float] = field(
        default_factory=lambda: _copy_hormone_map(DEFAULT_BASELINE)
    )
    recovery_rate: float = DEFAULT_RECOVERY_RATE
    interaction_rate: float = DEFAULT_INTERACTION_RATE
    time_scale: float = DEFAULT_TIME_SCALE
    interaction_matrix: dict[str, dict[str, float]] = field(
        default_factory=lambda: _copy_interaction_matrix(
            DEFAULT_INTERACTION_MATRIX
        )
    )

    def __post_init__(self) -> None:
        self.baseline = _copy_hormone_map(self.baseline)
        self.levels = self._normalized_levels(self.levels)
        self.set_time_scale(self.time_scale)

    def apply_delta(self, **deltas: float) -> None:
        for hormone, delta in deltas.items():
            self._ensure_known_hormone(hormone)
            self.levels[hormone] = _clamp_level(self.levels[hormone] + delta)

    def set_time_scale(self, time_scale: float) -> None:
        time_scale = float(time_scale)
        if time_scale < MIN_TIME_SCALE:
            raise ValueError("time_scale must be greater than or equal to 0.0")
        self.time_scale = time_scale

    def tick(self, dt: float = 1.0) -> None:
        dt = float(dt)
        if dt < 0.0:
            raise ValueError("dt must be greater than or equal to 0.0")

        self.levels = self._normalized_levels(self.levels)
        effective_dt = dt * self.time_scale
        if effective_dt == 0.0:
            return

        recovered = self._apply_recovery(effective_dt)
        interactions = self._calculate_interactions(recovered)

        self.levels = {
            hormone: _clamp_level(
                recovered[hormone]
                + interactions[hormone] * self.interaction_rate * effective_dt
            )
            for hormone in HORMONES
        }

    def snapshot(self) -> dict[str, float]:
        return dict(self.levels)

    def reset(self) -> None:
        self.levels = dict(self.baseline)

    def _apply_recovery(self, effective_dt: float) -> dict[str, float]:
        recovery_weight = min(1.0, self.recovery_rate * effective_dt)
        return {
            hormone: _clamp_level(
                level + (self.baseline[hormone] - level) * recovery_weight
            )
            for hormone, level in self.levels.items()
        }

    def _calculate_interactions(
        self, levels: Mapping[str, float]
    ) -> dict[str, float]:
        interactions = {hormone: 0.0 for hormone in HORMONES}

        for source_hormone, targets in self.interaction_matrix.items():
            self._ensure_known_hormone(source_hormone)
            source_deviation = levels[source_hormone] - self.baseline[
                source_hormone
            ]
            if source_deviation == 0.0:
                continue

            for target_hormone, weight in targets.items():
                self._ensure_known_hormone(target_hormone)
                interactions[target_hormone] += source_deviation * weight

        return interactions

    def _normalized_levels(
        self, source: Mapping[str, float]
    ) -> dict[str, float]:
        missing = [hormone for hormone in HORMONES if hormone not in source]
        if missing:
            raise ValueError(f"missing hormone levels: {', '.join(missing)}")
        return _copy_hormone_map(source)

    def _ensure_known_hormone(self, hormone: str) -> None:
        if hormone not in HORMONES:
            raise ValueError(f"unknown hormone: {hormone}")
