import games.dictator as d
import games.negotiation as n
import games.rockpaperscissors as rps

import json
import os

model_ids = [
    {
        "model_id" : "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "model_name" : "Claude 3.5 Sonnet v2",
    },
]

def test_negotiation():
    game = n.NegotiationGame(
        {"book" : 1, "hat" : 2, "ball" : 3},
        [
            {"book" : 1, "hat" : 3, "ball" : 1},
            {"book" : 2, "hat" : 1, "ball" : 2}
        ],
        "comp",
        model_ids[0]["model_id"],
        log_path=os.path.join("logs", model_ids[0]["model_name"], "negotiation"),
    )
    
    result = game.play()
    return result

def test_rockpaperscissors():
    game = rps.RockPaperScissorsGame(
        2,
        1,
        1,
        0,
        model_ids[0]["model_id"],
        log_path=os.path.join("logs", model_ids[0]["model_name"], "rockpaperscissors"),
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
        model_ids[0]["model_id"],
        log_path=os.path.join("logs", model_ids[0]["model_name"], "dictator"),
    )
    result = game.play()
    return result

if __name__ == "__main__":
    game_output = test_rockpaperscissors()
    print(json.dumps(game_output, indent=2))
