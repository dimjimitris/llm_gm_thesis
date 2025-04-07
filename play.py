from chat.player import (
    BedrockPlayer,
    SingleRoundEquilibriumPlayer,
    PatternPlayer,
    AdaptivePlayer,
    TitForTatPlayer,
)
from chat.rps import RockPaperScissorsGame
from chat.prompt import PromptGenerator
from descriptions.rps import (
    RPS_INIT_DEFAULT,
    RPS_INIT_SPP,
    RPS_INIT_COT,
    RPS_GAME_SETTINGS,
)

DESCRIPTIONS = {
    "default": RPS_INIT_DEFAULT,
    "spp": RPS_INIT_SPP,
    "cot": RPS_INIT_COT,
}

import os
import argparse
import time
import json
from threading import Thread

models = [
    {
        "model_id" : "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "model_name" : "Claude 3.5 Sonnet v2",
    },
    {
        "model_id" : "us.meta.llama3-3-70b-instruct-v1:0",
        "model_name" : "Llama 3.3 70B Instruct",
    },
    {
        "model_id" : "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "model_name" : "Claude 3.7 Sonnet",
    },
    #{
    #    "model_id" : "us.deepseek.r1-v1:0",
    #    "model_name" : "DeepSeek-R1",
    #},
]

def trial_rps(
    id: int,
    rounds: int,
    game_settings_type: str,
    game_settings: dict,
    model_id: str,
    model_name: str,
    temp: float,
    max_tokens: int,
    player_types: list[str],
    player_tot: list[int],
    log_root_dir : str,
):
    log_dir = os.path.join(log_root_dir, model_name)

    # create player objects
    players = list()
    for i, player_type in enumerate(player_types):
        if player_type in ["default", "spp", "cot"]:
            players.append(
                BedrockPlayer(
                    i,
                    PromptGenerator(
                        "rps",
                        game_settings,
                        DESCRIPTIONS[player_type],
                    ).get_prompt(),
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    player_type,
                    player_tot[i],
                    model_id,
                    temp,
                    max_tokens,
                )
            )
        elif player_type == "srep":
            players.append(
                SingleRoundEquilibriumPlayer(
                    i,
                    "",
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    game_settings,
                )
            )
        elif player_type == "pp":
            players.append(
                PatternPlayer(
                    i,
                    "",
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    [v for v in game_settings["move_mapping"].values()]
                )
            )
        elif player_type == "ap":
            players.append(
                AdaptivePlayer(
                    i,
                    "",
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    game_settings["move_mapping"],
                )
            )
        elif player_type == "tft":
            players.append(
                TitForTatPlayer(
                    i,
                    "",
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    game_settings["move_mapping"],
                )
            )

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

VALID_PLAYER_TYPES = ["default", "spp", "cot", "srep", "pp", "ap", "tft"]
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

    parser.add_argument(
        "-p1", "--player1",
        type=str,
        choices=VALID_PLAYER_TYPES,
        required=True,
        metavar="PLAYER1",
        help="Player 1 type\n  Options: " + " ".join(VALID_PLAYER_TYPES)
    )

    parser.add_argument(
        "-p2", "--player2",
        type=str,
        choices=VALID_PLAYER_TYPES,
        required=True,
        metavar="PLAYER2",
        help="Player 2 type\n  Options: " + " ".join(VALID_PLAYER_TYPES)
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
    player1_type = args.player1
    player2_type = args.player2

    # duration calculation
    start_time = time.time()

    game_outcome = trial_rps(
        trial_id,
        rounds,
        game_settings_type,
        game_settings,
        model_id,
        model_name,
        temp,
        1024,
        [player1_type, player2_type],
        [1, 1],
        "logs",
    )

    end_time = time.time()
    duration = end_time - start_time

    print(f"Game outcome: {json.dumps(game_outcome, indent=2)}")

    print(f"The script took {duration:.2f} seconds to run {rounds} rounds.\n")

def main2(iteration : int):
    threads : list[list[Thread]] = list()
    for model_id in VALID_MODEL_IDS:
        trial_idx = 0
        threads.append(list())
        for valid_game_setting in ["eq1", "p3"]:
            for player1_type, player2_type in [
                ("default", "default"),
                ("default", "spp"),
                ("default", "cot"),
                ("spp", "spp"),
                ("spp", "cot"),
                ("cot", "cot"),
                ("default", "srep"),
                ("default", "pp"),
                ("default", "ap"),
                ("default", "tft"),
                ("spp", "srep"),
                ("spp", "pp"),
                ("spp", "ap"),
                ("spp", "tft"),
                ("cot", "srep"),
                ("cot", "pp"),
                ("cot", "ap"),
                ("cot", "tft"),
            ]:
                threads[-1].append(
                    Thread(
                        name=f"Thread-{iteration}-{trial_idx}-{model_id}-{valid_game_setting}-{player1_type}-{player2_type}",
                        target=trial_rps,
                        args=(
                            trial_idx,
                            30,
                            valid_game_setting,
                            RPS_GAME_SETTINGS[valid_game_setting],
                            model_id,
                            next(model["model_name"] for model in models if model["model_id"] == model_id),
                            0.8,
                            4096,
                            [player1_type, player2_type],
                            [1, 1],
                            os.path.join("data", f"iteration_{iteration}"),
                        )
                    )
                )
                trial_idx += 1

    # do this in batches
    for i in range(4):
        for thread_list in threads:
            step = len(thread_list)//4
            for j in range(step*i, step*(i+1)):
                thread_list[j].start()

        for thread_list in threads:
            step = len(thread_list)//4
            for j in range(step*i, step*(i+1)):
                thread_list[j].join()

if __name__ == "__main__":
    for i in range(5):
        main2(i)