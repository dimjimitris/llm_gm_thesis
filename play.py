from chat.player import Player
from chat.rps import RockPaperScissorsGame
from descriptions.rps import RPS_DESC

import os
import argparse
import time
import json

game_settings : dict = RPS_DESC["game_settings"]

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

def trial_rps(
    id: int,
    rounds: int,
    game_setting: str,
    this_game_settings: dict,
    model_id: str,
    model_name: str,
):
    log_path = os.path.join("logs", model_name)

    r = this_game_settings["r"]
    p = this_game_settings["p"]
    s = this_game_settings["s"]

    # create a game object
    game = RockPaperScissorsGame(
        id,
        log_path,
        1.0,
        256,
        model_id,
        game_setting,
        r,
        p,
        s,
        this_game_settings["move_mapping"],
        True,
    )

    # create player objects
    players = [
        Player(
            i,
            game.system_prompt,
            os.path.dirname(game.game_log),
        ) for i in range(2)
    ]

    # add players to the game
    game.add_players(players[0], players[1])

    # play the game
    game_outcome = game.play(rounds)

    return game_outcome

def main():
    VALID_GAMES = ["rps"]
    VALID_GAME_SETTINGS = ["eq1", "eq2", "r2", "p2", "s2"]
    VALID_MODEL_IDS = [model["model_id"] for model in models]

    parser = argparse.ArgumentParser(description="Trial Rock-Paper-Scissors games")

    parser.add_argument(
        "-g",
        "--game",
        type=str,
        choices=VALID_GAMES,
        help=f"Game type (allowed: {', '.join(VALID_GAMES)})",
    )

    parser.add_argument(
        "-s",
        "--setting",
        type=str,
        choices=VALID_GAME_SETTINGS,
        help=f"Game setting (allowed: {', '.join(VALID_GAME_SETTINGS)})",
    )

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        choices=VALID_MODEL_IDS,
        help=f"Model ID (allowed: {', '.join(VALID_MODEL_IDS)})",
    )

    parser.add_argument(
        "-i",
        "--trial_id",
        type=int,
        default=0,
        help="Trial ID (default: 0)",
    )

    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=3,
        help="Number of rounds to play",
    )

    args = parser.parse_args()

    game_type = args.game
    game_setting = args.setting
    this_game_settings = game_settings[game_setting]
    model_id = args.model
    model_name = next(model["model_name"] for model in models if model["model_id"] == model_id)
    trial_id = args.trial_id
    rounds = args.rounds

    # duration calculation
    start_time = time.time()

    game_outcome = trial_rps(
        trial_id,
        rounds,
        game_setting,
        this_game_settings,
        model_id,
        model_name,
    )

    end_time = time.time()
    duration = end_time - start_time

    print(f"Game outcome: {json.dumps(game_outcome, indent=2)}")

    print(f"The script took {duration:.2f} seconds to run {rounds} rounds.\n")

if __name__ == "__main__":
    main()