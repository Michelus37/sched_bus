from engine import RoundEngine
from simulation import simulate
from strategy import HeuristicStrategy, RandomStrategy


if __name__ == "__main__":
    engine = RoundEngine(stake=500)

    print("Single round with HeuristicStrategy")
    strategy = HeuristicStrategy()
    ctx = engine.play_full_round(strategy=strategy, seed=1233)

    print("State:", ctx.state.name)
    print("Won:", ctx.is_won)
    print("Loss reason:", ctx.loss_reason)
    print("Drawn cards:", [str(card) for card in ctx.drawn_cards])
    print("Evaluations:")
    for evaluation in ctx.evaluations:
        print(evaluation.step, evaluation.success, evaluation.expected, evaluation.actual, evaluation.details)

    print("\nSimulation comparison:")
    print("Random:", simulate(rounds=5000, strategy=RandomStrategy(seed=99), seed=2))
    print("Heuristic:", simulate(rounds=5000, strategy=HeuristicStrategy(), seed=3))
