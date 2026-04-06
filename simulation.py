from __future__ import annotations

import random
from typing import Any, Optional

from engine import RoundEngine
from strategy import Strategy


DEFAULT_WIN_MULTIPLIER = 20


def simulate(
    rounds: int,
    strategy: Strategy,
    seed: Optional[int] = None,
    stake: int = 500,
    win_multiplier: int = DEFAULT_WIN_MULTIPLIER,
) -> dict[str, Any]:
    """Run many rounds and return performance metrics.

    Profit assumption used here:
    - loss  -> -stake
    - win   -> +(win_multiplier - 1) * stake

    Example with stake=500 and win_multiplier=20:
    - loss  -> -500
    - win   -> +9500 net profit
    """

    rng = random.Random(seed)
    engine = RoundEngine(stake=stake)
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

    gross_profit = 0
    for r in results:
        if r.is_won:
            gross_profit += (win_multiplier - 1) * stake
        else:
            gross_profit -= stake

    return {
        "rounds": rounds,
        "won": won,
        "lost": lost,
        "win_rate": won / rounds if rounds else 0.0,
        "losses_by_step": losses_by_step,
        "stake": stake,
        "win_multiplier": win_multiplier,
        "net_profit": gross_profit,
        "avg_profit_per_round": gross_profit / rounds if rounds else 0.0,
        "expected_value_per_stake": (gross_profit / rounds / stake) if rounds and stake else 0.0,
    }


def compare_strategies(
    rounds: int,
    strategies: dict[str, Strategy],
    seed: Optional[int] = None,
    stake: int = 500,
    win_multiplier: int = DEFAULT_WIN_MULTIPLIER,
) -> dict[str, dict[str, Any]]:
    """Compare multiple strategies on the same round count.

    Each strategy receives its own reproducible random round stream derived from
    the provided seed so the whole comparison stays deterministic.
    """

    rng = random.Random(seed)
    comparison: dict[str, dict[str, Any]] = {}

    for name, strategy in strategies.items():
        comparison[name] = simulate(
            rounds=rounds,
            strategy=strategy,
            seed=rng.randint(0, 10_000_000),
            stake=stake,
            win_multiplier=win_multiplier,
        )

    return comparison
