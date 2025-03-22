from chat.player import BedrockPlayer
from chat.rps import RockPaperScissorsGame
from chat.prompt import PromptGenerator
from descriptions.rps import (
    RPS_INIT_DEFAULT,
    RPS_INIT_SPP,
    RPS_GAME_SETTINGS,
)

import os
import argparse
import time
import json

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
    system_prompt_skeletons: list[str],
    game_settings_type: str,
    game_settings: dict,
    model_id: str,
    model_name: str,
    temp: float,
):
    log_dir = os.path.join("logs", model_name)

    # create player objects
    players = [
        BedrockPlayer(
            0,
            PromptGenerator(
                "rps",
                game_settings,
                system_prompt_skeletons[0],
            ).get_prompt(),
            os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
            model_id,
            temp,
            1024,
        ),
        BedrockPlayer(
            1,
            PromptGenerator(
                "rps",
                game_settings,
                system_prompt_skeletons[1],
            ).get_prompt(),
            os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
            model_id,
            temp,
            1024,
        ),
    ]

    # create a game object
    game = RockPaperScissorsGame(
        id,
        players,
        game_settings_type,
        game_settings,
        log_dir,
        True,
    )

    # play the game
    game_outcome = game.play(rounds)

    return game_outcome

VALID_GAMES = ["rps"]
VALID_GAME_SETTINGS = [k for k in RPS_GAME_SETTINGS.keys()]
VALID_MODEL_IDS = [model["model_id"] for model in models]

def argument_parser() -> argparse.Namespace:
    """
    Argument parser for the script

    Returns:
        argparse.Namespace: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Rock-Paper-Scissors Game Simulator",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  play.py -g rps -s eq1 -m anthropic.claude-3-5-sonnet-20241022-v2:0
  play.py -g rps -s p2 -m us.meta.llama3-3-70b-instruct-v1:0 -t 1.0 -r 5 -i 42
        """
    )
    
    parser.add_argument(
        "-g", "--game",
        type=str,
        choices=VALID_GAMES,
        required=True,
        metavar="GAME",
        help="Game type\n  Options: " + " ".join(VALID_GAMES)
    )
    
    parser.add_argument(
        "-s", "--setting",
        type=str,
        choices=VALID_GAME_SETTINGS,
        required=True,
        metavar="SETTING",
        help="Game setting\n  Options: " + " ".join(VALID_GAME_SETTINGS)
    )
    
    parser.add_argument(
        "-m", "--model",
        type=str,
        choices=VALID_MODEL_IDS,
        required=True,
        metavar="MODEL_ID",
        help="LLM model ID\n  Options:\n    " + "  \n    ".join(VALID_MODEL_IDS)
    )

    parser.add_argument(
        "-t", "--temp",
        type=float,
        default=0.8,
        metavar="TEMP",
        help="Sampling temperature (default: 0.8)"
    )
    
    parser.add_argument(
        "-i", "--trial_id",
        type=int,
        default=0,
        metavar="TRIAL_ID",
        help="Trial identifier (default: 0)"
    )
    
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=3,
        metavar="ROUNDS",
        help="Number of rounds (default: 3)"
    )

    return parser.parse_args()

def main():
    args = argument_parser()

    game_type = args.game
    game_settings_type = args.setting
    game_settings = RPS_GAME_SETTINGS[game_settings_type]
    model_id = args.model
    temp = args.temp
    model_name = next(model["model_name"] for model in models if model["model_id"] == model_id)
    trial_id = args.trial_id
    rounds = args.rounds

    # duration calculation
    start_time = time.time()

    game_outcome = trial_rps(
        trial_id,
        rounds,
        [RPS_INIT_SPP, RPS_INIT_DEFAULT],
        game_settings_type,
        game_settings,
        model_id,
        model_name,
        temp,
    )

    end_time = time.time()
    duration = end_time - start_time

    print(f"Game outcome: {json.dumps(game_outcome, indent=2)}")

    print(f"The script took {duration:.2f} seconds to run {rounds} rounds.\n")

if __name__ == "__main__":
    main()