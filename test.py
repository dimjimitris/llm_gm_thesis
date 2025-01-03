import games.dictator as d
import games.negotiation as n
import games.rockpaperscissors as rps

import json
import os

models = [
    {
        "model_id" : "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "model_name" : "Claude 3.5 Sonnet v2",
    },
    {
        "model_id" : "us.meta.llama3-3-70b-instruct-v1:0",
        "model_name" : "Llama 3.3 70B Instruct",
    },
]

def test_negotiation(idx):
    model = models[idx]
    game = n.NegotiationGame(
        {"book" : 1, "hat" : 2, "ball" : 3},
        [
            {"book" : 1, "hat" : 3, "ball" : 1},
            {"book" : 2, "hat" : 1, "ball" : 2}
        ],
        "semi",
        model["model_id"],
        log_path=os.path.join("logs", model["model_name"], "negotiation"),
    )
    
    result = game.play()
    return result

def test_rockpaperscissors(idx):
    model = models[idx]
    game = rps.RockPaperScissorsGame(
        1,
        1,
        1,
        0,
        model["model_id"],
        log_path=os.path.join("logs", model["model_name"], "rockpaperscissors"),
    )
    result = game.play()
    return result

def test_dictator_game(idx):
    model = models[idx]
    game = d.DictatorGame(
        [
            [-400, -900],
            [-401, -200],
        ],
        "minimize",
        model["model_id"],
        log_path=os.path.join("logs", model["model_name"], "dictator"),
    )
    result = game.play()
    return result

if __name__ == "__main__":
    #idx = int(input("Enter model index: "))
    #game_output = test_dictator_game(idx)
    #print(json.dumps(game_output, indent=2))

    l = { "hello" : 1, "world" : 2}

    if "hello" in l:
        print(l["hello"])