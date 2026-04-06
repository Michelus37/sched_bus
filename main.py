from engine import RoundEngine
from simulation import compare_strategies, simulate
from strategy import HeuristicStrategy, LookaheadStrategy, RandomStrategy


if __name__ == "__main__":
    engine = RoundEngine(stake=500)

    print("Single round with LookaheadStrategy")
    strategy = LookaheadStrategy()
    ctx = engine.play_full_round(strategy=strategy, seed=1233)

    print("State:", ctx.state.name)
    print("Won:", ctx.is_won)
    print("Loss reason:", ctx.loss_reason)
    print("Drawn cards:", [str(card) for card in ctx.drawn_cards])
    print("Evaluations:")
    for evaluation in ctx.evaluations:
        print(evaluation.step, evaluation.success, evaluation.expected, evaluation.actual, evaluation.details)

    print("\nSingle strategy metrics:")
    print("Heuristic:", simulate(rounds=5000, strategy=HeuristicStrategy(), seed=3, stake=500, win_multiplier=20))
    #bullshit strategy
    #print("Lookahead:", simulate(rounds=5000, strategy=LookaheadStrategy(), seed=4, stake=500, win_multiplier=20))

    print("\nSimulation comparison:")
    comparison = compare_strategies(
        rounds=5000,
        strategies={
            "random": RandomStrategy(seed=99),
            "heuristic": HeuristicStrategy(),
            #"lookahead": LookaheadStrategy(),
        },
        seed=2,
        stake=500,
        win_multiplier=20,
    )
    for name, result in comparison.items():
        print(name, result)
