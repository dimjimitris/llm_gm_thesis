def optimal_strategy(
    p : int,
    r : int,
    s : int,
):
    return {
        "rock": s / (p + r + s),
        "paper": r / (p + r + s),
        "scissors": p / (p + r + s),
    }