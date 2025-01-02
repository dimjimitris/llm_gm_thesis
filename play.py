from games.negotiation import NegotiationGame
from games.rockpaperscissors import RockPaperScissorsGame
from games.dictator import DictatorGame

import os
import random
import argparse
import time
import numpy as np

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

def trial_negotiation(
    objective : str,
    model_id : str,
    model_name : str,
):
    # this function simulates one trial of the negotiation game

    def parse_context(context : str):
        context = context.split()
        counts = [int(n) for n in context[0::2]]
        values = [int(v) for v in context[1::2]]
        return counts, values

    # sample from possible game contexts
    with open(os.path.join("data", "negotiation_selfplay.txt")) as file:
        lines = [line.strip() for line in file]

    random_indice = random.randint(0, 4085)
    cnts, vals1 = parse_context(lines[random_indice * 2])
    _, vals2 = parse_context(lines[random_indice * 2 + 1])
    
    keys = ["book", "hat", "ball"]

    log_path = os.path.join("logs", model_name, "negotiation")

    game = NegotiationGame(
        {keys[i] : cnts[i] for i in range(3)},
        [
            {keys[i] : vals1[i] for i in range(3)},
            {keys[i] : vals2[i] for i in range(3)}
        ],
        objective,
        model_id,
        log_path=log_path,
    )

    game_outcome = game.play()

    for i in range(game.player_count):
        with open(os.path.join(log_path, f"agent_{i}_scores"), "a") as f:
            f.write(f"{game_outcome[f"player_{i}_points"]} \n")

    return game_outcome

def trial_rockpaperscissors(
    model_id : str,
    model_name : str,
):
    # this function simulates one trial of the rock-paper-scissors game    

    def parse_context(context : str):
        context = [int(v) for v in context.split()]
        return context
    
    # sample from possible game contexts
    with open(os.path.join("data", "rockpaperscissors_selfplay.txt")) as file:
        lines = [line.strip() for line in file]

    random_indice = random.randint(0, 4)
    vals = parse_context(lines[random_indice])
    tie = vals[0]
    paper_beats_rock = vals[1]
    rock_beats_scissors = vals[2]
    scissors_beats_paper = vals[3]

    log_path = os.path.join("logs", model_name, "rockpaperscissors")

    game = RockPaperScissorsGame(
        paper_beats_rock,
        rock_beats_scissors,
        scissors_beats_paper,
        tie,
        model_id,
        log_path=log_path,
    )

    game_outcome = game.play()

    for i in range(game.player_count):
        with open(os.path.join(log_path, f"agent_{i}_scores"), "a") as f:
            f.write(f"{game_outcome[f"player_{i}_points"]} \n")

    return game_outcome

def trial_dictator(
    model_id : str,
    model_name : str,
):
    # this function simulates one trial of the dictator game

    with open(os.path.join("data", "dictator_selfplay.txt")) as file:
        lines = [line.strip() for line in file]

    random_indice = random.randint(0, 19)
    vals1 = [int(v) for v in lines[random_indice * 3].split()]
    vals2 = [int(v) for v in lines[random_indice * 3 + 1].split()]
    objective = None
    if lines[random_indice * 3 + 2].strip() == "M":
        objective = "maximize"
    elif lines[random_indice * 3 + 2].strip() == "m":
        objective = "minimize"
    else:
        raise ValueError("Invalid objective")
    
    log_path = os.path.join("logs", model_name, "dictator")

    game = DictatorGame(
        [vals1, vals2],
        objective,
        model_id,
        log_path=log_path,
    )

    game_outcome = game.play()

    for i in range(2):
        with open(os.path.join(log_path, f"agent_{i}_scores"), "a") as f:
            f.write(f"{game_outcome[f"player_{i}_points"]} \n")

    return game_outcome
    
def main():
    VALID_GAMES = ["negotiation", "rockpaperscissors", "dictator"]
    VALID_OBJECTIVES_NEGOTIATION = ["semi", "coop", "comp"]
    VALID_MODEL_IDS = [model["model_id"] for model in models]

    # parse CLI for objective and model ID
    parser = argparse.ArgumentParser(
        description="A script that demonstrates argparse usage"
    )

    parser.add_argument(
        "-g",
        "--game",
        type=str,
        choices=VALID_GAMES,
        help=f"Game type (allowed: {', '.join(VALID_GAMES)})"
    )
    parser.add_argument(
        "-o",
        "--objective",
        type=str,
        choices=VALID_OBJECTIVES_NEGOTIATION + ["none"],
        help=f"Game objective (allowed: {', '.join(VALID_OBJECTIVES_NEGOTIATION)} for negotiation, 'none' for other games)"
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        choices=VALID_MODEL_IDS,
        help=f"Model ID (allowed : {', '.join(VALID_MODEL_IDS)})")
    parser.add_argument("-n", "--num_runs", type=int, help="Number of self-play games")
    
    args = parser.parse_args()

    game_type = args.game
    objective = args.objective

    model_id = args.model
    model_name = None
    for model in models:
        if model["model_id"] == model_id:
            model_name = model["model_name"]
            break

    num_runs = args.num_runs

    # duration calculation
    start_time = time.time()

    agent_outcomes = [list(), list()]

    for _ in range(num_runs):
        game_outcome = None
        if game_type == "negotiation":
            game_outcome = trial_negotiation(objective, model_id, model_name)
        elif game_type == "rockpaperscissors":
            game_outcome = trial_rockpaperscissors(model_id, model_name)
        elif game_type == "dictator":
            game_outcome = trial_dictator(model_id, model_name)
        else:
            raise ValueError("Invalid game type")
        
        for i in range(2):
            agent_outcomes[i].append(game_outcome[f"player_{i}_points"])

    # print mean of points
    for i in range(2):
        print(f"player_{i} mean: {np.mean(agent_outcomes[i])}")

    end_time = time.time()

    duration = end_time - start_time
    print(f"The script took {duration} seconds to run {num_runs} games")

if __name__ == "__main__":
    main()

