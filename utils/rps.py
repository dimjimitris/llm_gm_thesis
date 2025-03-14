def optimal_strategy(
    r : int,
    p : int,
    s : int,
):
    """
    r : rock beats scissors giving the winner r points and the loser -r points
    p : paper beats rock giving the winner p points and the loser -p points
    s : scissors beats paper giving the winner s points and the loser -s points
    ties give 0 points to both players

    The payoff matrix is given below:

    | payoff   | rock        | paper       | scissors    |
    |----------|-------------|-------------|-------------|
    | rock     |   (0, 0)    |   (-p, p)   |   (r, -r)   |
    | paper    |   (p, -p)   |   (0, 0)    |   (-s, s)   |
    | scissors |   (-r, r)   |   (s, -s)   |   (0, 0)    |

    This function calculates the Mixed Nash Equilibrium strategy a player
    should follow, when playing one round of rock-paper-scissors against an
    unknown opponent given the above payoff matrix.

    Parameters
    ----------
    r : int
        reward of rock beating scissors
    p : int
        reward of paper beating rock
    s : int
        reward of scissors beating paper
    """
    return {
        "rock": s / (p + r + s),
        "paper": r / (p + r + s),
        "scissors": p / (p + r + s),
    }