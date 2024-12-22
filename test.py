import games.dictator as d
import games.negotiation as n
import games.rockpaperscissors as rps

from tabulate import tabulate

def test_dictator():
    game = d.DictatorGame(
        100,
        300,
        300,
        100,
        maximize=True
    )
    
    print(game.context[0]['content']['text'])

def test_negotiation():
    game = n.NegotiationGame(
        {"book" : 1, "hat" : 2, "ball" : 3},
        [
            {"book" : 3, "hat" : 0, "ball" : 1},
            {"book" : 2, "hat" : 2, "ball" : 0}
        ],
        "semi"
    )
    
    print(game.contexts[0][0]['content']['text'])

def test_rockpaperscissors():
    game = rps.RockPaperScissorsGame(
        1,
        1,
        1,
        0
    )
    
    print(game.contexts[0][0]['content']['text'])

def x():
    return

if __name__ == "__main__":
    #test_dictator()
    #test_negotiation()
    #test_rockpaperscissors()

    tie = 0
    r = 1
    p = 1
    s = 1

    print(
        tabulate(
            tabular_data=[
                ["rock", (tie, tie), (-p, p), (r, -r)],
                ["paper", (p, -p), (tie, tie), (-s, s)],
                ["scissors", (-r, r), (s, -s), (tie, tie)]
            ],
            headers=["", "rock", "paper", "scissors"],
            tablefmt="github"
        )
    )