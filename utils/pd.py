def optimal_strategy(
    aa : int,
    ab : int,
    ba : int,
    bb : int,
):
    """
    aa : a paired with a giving aa points
    ab : a paired with b giving ab points
    ba : b paired with a giving ba points
    bb : b paired with b giving bb points

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
        reward of a paired with a
    ab : int
        reward of a paired with b
    ba : int
        reward of b paired with a
    bb : int
        reward of b paired with b
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
            "a": (bb - ab) / (aa - ab + bb - ba),
            "b": (aa - ba) / (aa - ab + bb - ba),
        }