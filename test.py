import games.dictator as d
import games.negotiation as n
import games.rockpaperscissors as rps

import boto3
import json

def test_negotiation():
    game = n.NegotiationGame(
        {"book" : 1, "hat" : 2, "ball" : 3},
        [
            {"book" : 1, "hat" : 3, "ball" : 1},
            {"book" : 2, "hat" : 1, "ball" : 2}
        ],
        "comp"
    )
    
    result = game.play()
    return result

def test_rockpaperscissors():
    game = rps.RockPaperScissorsGame(
        2,
        1,
        1,
        0
    )
    result = game.play()
    return result

def test_dictator_game():
    game = d.DictatorGame(
        -400, -900,
        -401, -200,
        False,
    )
    result = game.play()
    return result

if __name__ == "__main__":
    game_output = test_dictator_game()
    print(json.dumps(game_output, indent=2))
