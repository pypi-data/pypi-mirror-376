from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(slots=True)
class SundewConfig:
    """
    Configuration for the Sundew algorithm.

    Call `validate()` to perform basic sanity checks on the values.
    """

    # Activation & rate control
    activation_threshold: float = 0.70
    target_activation_rate: float = 0.25
    ema_alpha: float = 0.10

    # PI controller
    adapt_kp: float = 0.08
    adapt_ki: float = 0.02
    error_deadband: float = 0.005
    integral_clamp: float = 0.50

    # Threshold bounds
    min_threshold: float = 0.20
    max_threshold: float = 0.90

    # Energy pressure & gating
    energy_pressure: float = 0.03
    gate_temperature: float = 0.10

    # Energy model
    max_energy: float = 100.0
    dormant_tick_cost: float = 0.5
    dormancy_regen: Tuple[float, float] = (1.0, 3.0)  # (min, max) regen per dormant tick
    eval_cost: float = 0.6
    base_processing_cost: float = 10.0

    # Significance weights (should sum to 1.0 for a convex combination)
    w_magnitude: float = 0.30
    w_anomaly: float = 0.40
    w_context: float = 0.20
    w_urgency: float = 0.10

    # Misc
    rng_seed: int = 42

    # Optional features
    refractory: int = 0  # ticks to sleep after activation
    probe_every: int = 0  # force a probe every N events (0=off)

    def validate(self) -> None:
        """Raise ValueError if any checks fail."""
        if not (0.0 <= self.min_threshold <= self.max_threshold <= 1.0):
            raise ValueError("min_threshold must be ≤ max_threshold within [0, 1].")
        if self.gate_temperature < 0.0:
            raise ValueError("gate_temperature must be non-negative.")
        if not (0.0 <= self.target_activation_rate <= 1.0):
            raise ValueError("target_activation_rate must be in [0, 1].")

        for name in (
            "ema_alpha",
            "adapt_kp",
            "adapt_ki",
            "error_deadband",
            "integral_clamp",
            "energy_pressure",
            "max_energy",
            "dormant_tick_cost",
            "eval_cost",
            "base_processing_cost",
            "w_magnitude",
            "w_anomaly",
            "w_context",
            "w_urgency",
        ):
            value = getattr(self, name)
            if value < 0:
                raise ValueError(f"{name} must be non-negative.")

        # Enforce convex combination for weights
        weight_sum = self.w_magnitude + self.w_anomaly + self.w_context + self.w_urgency
        if abs(weight_sum - 1.0) > 1e-6:
            raise ValueError("w_magnitude + w_anomaly + w_context + w_urgency must sum to 1.0.")
