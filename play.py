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
    RPS_INIT_ZS,
    RPS_INIT_SPP,
    RPS_INIT_COT,
    RPS_SETTINGS_COLLECTION,
)

DESCRIPTIONS = {
    "default": RPS_INIT_ZS,
    "spp": RPS_INIT_SPP,
    "cot": RPS_INIT_COT,
}

import os
from threading import Thread

models = [
    {
        "id" : "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name" : "Claude 3.5 Sonnet v2",
        "thinking" : False,
    },
    {
        "id" : "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "name" : "Claude 3.7 Sonnet",
        "thinking" : False,
    },
    {
        "id" : "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "name" : "Claude 3.7 Sonnet (Thinking)",
        "thinking" : True,
    },
    {
        "id" : "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "name" : "Claude Sonnet 4",
        "thinking" : False,
    },
    {
        "id" : "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "name" : "Claude Sonnet 4 (Thinking)",
        "thinking" : True,
    },
    {
        "id" : "meta.llama3-1-405b-instruct-v1:0",
        "name" : "Llama 3.1 405B Instruct",
        "thinking" : False,
    },
    {
        "id" : "us.meta.llama3-3-70b-instruct-v1:0",
        "name" : "Llama 3.3 70B Instruct",
        "thinking" : False,
    },
    {
        "id" : "mistral.mistral-large-2407-v1:0",
        "name" : "Mistral Large (24.07)",
        "thinking" : False,
    },
    {
        "id" : "us.deepseek.r1-v1:0",
        "name" : "DeepSeek-R1",
        "thinking" : False,
    },
]

def trial_rps(
    id: str,
    rounds: int,
    game_settings_type: str,
    game_settings: dict,
    model: dict,
    temp: float,
    max_tokens: int,
    player_types: list[str],
    player_sc: list[int],
    log_root_dir : str,
):
    log_dir = os.path.join(log_root_dir, model["name"])

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
                    player_sc[i],
                    model["id"],
                    temp,
                    max_tokens,
                    model["thinking"],
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
                    ["scissors", "rock", "paper"],
                )
            )
        elif player_type == "ap":
            players.append(
                AdaptivePlayer(
                    i,
                    "",
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    game_settings,
                )
            )
        elif player_type == "tft":
            players.append(
                TitForTatPlayer(
                    i,
                    "",
                    os.path.join(log_dir, "rps", game_settings_type, f"rps_{id}"),
                    game_settings,
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
VALID_GAME_SETTINGS = [k for k in RPS_SETTINGS_COLLECTION.keys()]

def main2_aux(iteration : int, self_consistency : bool) -> dict[str, list[Thread]]:
    threads : dict[str, list[Thread]] = {}
    for model in models:
        threads_list = list()
        #trial_idx = 200
        for valid_game_setting in VALID_GAME_SETTINGS:
            for player1_type, player2_type in [
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


                ("default", "default"),
                ("default", "spp"),
                ("default", "cot"),
                
                ("spp", "default"),
                ("spp", "spp"),
                ("spp", "cot"),

                ("cot", "default"),
                ("cot", "spp"),
                ("cot", "cot"),
            ]:
                threads_list.append(
                    Thread(
                        name=f"Thread-{iteration}-{model["id"]}-{valid_game_setting}-{player1_type}-{player2_type}",
                        target=trial_rps,
                        args=(
                            f"{player1_type}_{player2_type}",
                            24,
                            valid_game_setting,
                            RPS_SETTINGS_COLLECTION[valid_game_setting],
                            model,
                            1.0,
                            4096,
                            [player1_type, player2_type],
                            [1, 1] if not self_consistency else [5, 1],
                            os.path.join("logs", "logs_3", "data" if not self_consistency else "data_tot", f"iteration_{iteration}"),
                        )
                    )
                )
                #trial_idx += 1

                # create directory for the model:
                #log_dir = os.path.join(
                #    "logs",
                #    "logs_3",
                #    "data" if not self_consistency else "data_tot",
                #    f"iteration_{iteration}",
                #    model["name"],
                #    "rps",
                #    valid_game_setting,
                #    f"rps_{player1_type}_{player2_type}"
                #)
                #os.makedirs(log_dir, exist_ok=True)

        threads[model["name"]] = threads_list

    return threads

def main2_remainder(root_dir: str, rounds: int):
    """
    Find all subdirectories in the given root directory that do not have enough valid games
    """
    threads = dict[str, list[Thread]]()

    import os
    import json
    for root, dirs, _ in os.walk(root_dir):
        for dir in dirs:
            if not dir.startswith("rps_"):
                continue
            dir_path = os.path.join(root, dir)

            flag = False

            if not os.path.isfile(os.path.join(dir_path, "game.json")):
                #print(f"Directory {dir_path} does not contain game.json")\
                flag = True
            else:
                with open(os.path.join(dir_path, "game.json"), "r") as f:
                    game_data = json.load(f)
                    rounds_played = game_data.get("valid_outcomes", [])
                    if len(rounds_played) < rounds: #or not all(rounds_played):
                        #print(f"Directory {dir_path} has only {len(rounds_played)} rounds, expected {rounds}")
                        # check if all values in valid_outcomes are true
                        #if not all(rounds_played):
                        #    print(f"Directory {dir_path} has incomplete rounds: {rounds_played}")
                        # get info from the directory name
                        flag = True

            if flag:
                self_consistency, iteration, model_name, game_type, game_settings_type, player_types = get_info(dir_path)
                if iteration is None or model_name is None or game_type is None or game_settings_type is None or player_types is None:
                    print(f"Directory {dir_path} does not have a valid name format")
                    continue

                #if model_name in ["Claude Sonnet 4", "Llama 3.1 405B Instruct"]:
                #    # skip models that are in the above list
                #    continue

                if model_name not in threads:
                    threads[model_name] = []
                threads[model_name].append(
                    Thread(
                        name=f"Thread-{iteration}-{model_name}-{game_type}-{game_settings_type}-{player_types}",
                        target=trial_rps,
                        args=(
                            f"{player_types[0]}_{player_types[1]}",
                            rounds,
                            game_settings_type,
                            RPS_SETTINGS_COLLECTION[game_settings_type],
                            models[[m["name"] for m in models].index(model_name)],
                            1.0,
                            6144,
                            player_types,
                            [1, 1] if not self_consistency else [5, 1],
                            os.path.join("logs", "logs_3", "data" if not self_consistency else "data_tot", f"iteration_{iteration}"),
                        )
                    )
                )
        
    return threads

# directories are of the format data{_tot}/iteration_{i}/model_name/game_type/game_settings_type/pd_{player1_type}_{player2_type}
def get_info(filename: str) -> tuple[str, str, str, str, str]:

    parts = filename.split(os.sep)
    if len(parts) < 6:
        return None, None, None, None, None, None
    
    sc = parts[-6]
    if sc != "data" and sc != "data_tot":
        return None, None, None, None, None, None

    if sc == "data_tot":
        sc = True
    else:
        sc = False
    iteration = parts[-5]
    # get iteration number from iteration_{i}
    if not iteration.startswith("iteration_"):
        return None, None, None, None, None, None
    iteration = iteration[len("iteration_"):]
    if not iteration.isdigit():
        return None, None, None, None, None
    iteration = int(iteration)
    model_name = parts[-4]
    game_type = parts[-3]
    game_settings_type = parts[-2]
    player_types = parts[-1].split("_")
    player_types = player_types[1:]
    if len(player_types) != 2:
        return None, None, None, None, None, None
    return sc, iteration, model_name, game_type, game_settings_type, player_types


def main2(iterations: int, self_consistency: bool):
    threads = dict[str, list[Thread]]()
    # create threads for each model and game settings
    for i in range(iterations):
        threads_aux = main2_aux(i, self_consistency)
        for model_name, model_threads in threads_aux.items():
            if model_name not in threads:
                threads[model_name] = []
            threads[model_name].extend(model_threads)

    # create threads to run exec_threads for each model's threads
    exec_threads_list : list[Thread] = list()
    for model_name, model_threads in threads.items():
        exec_threads_list.append(
            Thread(
                name=f"Exec-Threads-{model_threads[0].name}",
                target=exec_threads,
                args=(model_threads, 4)
            )
        )
    
    # start all exec_threads threads
    for exec_thread in exec_threads_list:
        exec_thread.start()

    # wait for all exec_threads threads to finish
    for exec_thread in exec_threads_list:
        exec_thread.join()

def main2_r(root_dir: str, rounds: int):
    threads = main2_remainder(root_dir, rounds)

    # create threads to run exec_threads for each model's threads
    exec_threads_list : list[Thread] = list()
    for model_name, model_threads in threads.items():
        exec_threads_list.append(
            Thread(
                name=f"Exec-Threads-{model_threads[0].name}",
                target=exec_threads,
                args=(model_threads, 3)
            )
        )
    
    # start all exec_threads threads
    for exec_thread in exec_threads_list:
        exec_thread.start()

    # wait for all exec_threads threads to finish
    for exec_thread in exec_threads_list:
        exec_thread.join()

def exec_threads(threads: list[Thread], count: int):
    import time
    #idx = 0
    #for i in range(partition):
    #    for thread in threads[idx:idx + len(threads) // partition]:
    #        thread.start()
    #        thread.join()
#
    #    idx += len(threads) // partition

    # execute count threads at a time, when one finishes, start the next one
    running : list[Thread] = []

    for _ in range(min(count, len(threads))):
        t = threads.pop(0)
        t.start()
        running.append(t)

    while threads: #or any(t.is_alive() for t in running):
        # check for finished threads
        for t in running[:]:
            if not t.is_alive():
                running.remove(t)
                if threads:
                    new_thread = threads.pop(0)
                    new_thread.start()
                    running.append(new_thread)
        time.sleep(5.0)

if __name__ == "__main__":
    main2_r("logs/logs_3", 24)