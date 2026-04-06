from engine import RoundEngine
from simulation import simulate
from strategy import RandomStrategy


if __name__ == "__main__":
    engine = RoundEngine(stake=500)
    strategy = RandomStrategy(seed=42)

    ctx = engine.play_full_round(strategy=strategy, seed=123)

    print("State:", ctx.state.name)
    print("Won:", ctx.is_won)
    print("Loss reason:", ctx.loss_reason)
    print("Drawn cards:", [str(card) for card in ctx.drawn_cards])
    print("Evaluations:")
    for evaluation in ctx.evaluations:
        print(vars(evaluation))

    print("\nSimulation:")
    print(simulate(rounds=1000, strategy=RandomStrategy(seed=99), seed=1))
