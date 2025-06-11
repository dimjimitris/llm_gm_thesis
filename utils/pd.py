def optimal_strategy(
    aa : int,
    ab : int,
    ba : int,
    bb : int,
):
    """
    aa : a cooperating with a giving aa points
    ab : a cooperating with b giving ab points
    ba : b cooperating with a giving ba points
    bb : b cooperating with b giving bb points

    The payoff matrix is given below:

    | payoff   |      a      |      b      |
    |----------|-------------|-------------|
    |    a     |  (aa, aa)   |  (ab, ba)   |
    |    b     |  (ba, ab)   |  (bb, bb)   |

    This function calculates the Mixed Nash Equilibrium strategy a player
    should follow, when playing one round of rock-paper-scissors against an
    unknown opponent given the above payoff matrix.

    Parameters
    ----------
    aa : int
        reward of a cooperating with a
    ab : int
        reward of a cooperating with b
    ba : int
        reward of b cooperating with a
    bb : int
        reward of b cooperating with b
    """
    if ba > aa and aa > bb and bb > ab and 2 * aa > ba + ab:
        # Prisoner's Dilemma
        return {
            "a": 0.0,
            "b": 1.0,
        }
    elif aa > ba and ba >= bb and bb > ab:
        # Stag Hunt
        return {
            "a": (ba - ab) / (aa - ab + ba - bb),
            "b": (aa - bb) / (aa - ab + ba - bb),
        }