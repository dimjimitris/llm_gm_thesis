import games.dictator as d
import games.negotiation as n
import games.rockpaperscissors as rps

import json

model_ids = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
]

def test_negotiation():
    game = n.NegotiationGame(
        {"book" : 1, "hat" : 2, "ball" : 3},
        [
            {"book" : 1, "hat" : 3, "ball" : 1},
            {"book" : 2, "hat" : 1, "ball" : 2}
        ],
        "comp",
        model_ids[0],
    )
    
    result = game.play()
    return result

def test_rockpaperscissors():
    game = rps.RockPaperScissorsGame(
        2,
        1,
        1,
        0,
        model_ids[0],
    )
    result = game.play()
    return result

def test_dictator_game():
    game = d.DictatorGame(
        [
            [-400, -900],
            [-401, -200],
        ],
        "minimize",
        model_ids[0],
    )
    result = game.play()
    return result

if __name__ == "__main__":
    game_output = test_dictator_game()
    print(json.dumps(game_output, indent=2))
