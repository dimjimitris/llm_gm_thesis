def optimal_strategy(
    ac : int,
    ba : int,
    cb : int,
):
    """
    ac : a beats c giving the winner ac points and the loser -ac points
    ba : b beats a giving the winner ba points and the loser -ba points
    cb : c beats b giving the winner cb points and the loser -cb points
    ties give 0 points to both players

    The payoff matrix is given below:

    | payoff   |      a      |      b      |      c      |
    |----------|-------------|-------------|-------------|
    |    a     |  (0, 0)     |  (-ba, ba)  |  (ac, -ac)  |
    |    b     |  (ba, -ba)  |  (0, 0)     |  (-cb, cb)  |
    |    c     |  (-ac, ac)  |  (cb, -cb)  |  (0, 0)     |

    This function calculates the Mixed Nash Equilibrium strategy a player
    should follow, when playing one round of rock-paper-scissors against an
    unknown opponent given the above payoff matrix.

    Parameters
    ----------
    ac : int
        reward of a beating c
    ba : int
        reward of b beating a
    cb : int
        reward of c beating b
    """
    return {
        "a": cb / (ba + ac + cb),
        "b": ac / (ba + ac + cb),
        "c": ba / (ba + ac + cb),
    }