from __future__ import annotations

import random
from typing import Any, Optional

from engine import RoundEngine
from strategy import Strategy


def simulate(rounds: int, strategy: Strategy, seed: Optional[int] = None) -> dict[str, Any]:
    rng = random.Random(seed)
    engine = RoundEngine()
    results = []

    for _ in range(rounds):
        round_seed = rng.randint(0, 10_000_000)
        ctx = engine.play_full_round(strategy=strategy, seed=round_seed)
        results.append(ctx)
        

    won = sum(1 for r in results if r.is_won)
    lost = rounds - won

    losses_by_step = {
        "step1_failed": 0,
        "step2_failed": 0,
        "step3_failed": 0,
        "step4_failed": 0,
    }
    for r in results:
        if r.loss_reason in losses_by_step:
            losses_by_step[r.loss_reason] += 1

    return {
        "rounds": rounds,
        "won": won,
        "lost": lost,
        "win_rate": won / rounds if rounds else 0.0,
        "losses_by_step": losses_by_step,
    }
