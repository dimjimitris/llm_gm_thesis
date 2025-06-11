from chat.player import (
    BedrockPlayer,
    SrepPD,
    PatternPlayer,
    MaximizerFreqP,
    TftPD,
)
from chat.pd import PrisonersDilemma
from chat.prompt import PromptGenerator
from descriptions.pd import (
    PD_INIT_ZS,
    PD_INIT_SPP,
    PD_INIT_COT,
    PD_SETTINGS_COLLECTION,
)

DESCRIPTIONS = {
    "zs": PD_INIT_ZS,
    "spp": PD_INIT_SPP,
    "cot": PD_INIT_COT,
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
    #{
    #    "id" : "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    #    "name" : "Claude 3.7 Sonnet (Thinking)",
    #    "thinking" : True,
    #},
    {
        "id" : "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "name" : "Claude Sonnet 4",
        "thinking" : False,
    },
    #{
    #    "id" : "us.anthropic.claude-sonnet-4-20250514-v1:0",
    #    "name" : "Claude Sonnet 4 (Thinking)",
    #    "thinking" : True,
    #},
    #{
    #    "id" : "meta.llama3-1-405b-instruct-v1:0",
    #    "name" : "Llama 3.1 405B Instruct",
    #    "thinking" : False,
    #},
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

def trial_pd(
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
        if player_type in ["zs", "spp", "cot"]:
            players.append(
                BedrockPlayer(
                    i,
                    PromptGenerator(
                        "pd",
                        game_settings,
                        DESCRIPTIONS[player_type],
                    ).get_prompt(),
                    os.path.join(log_dir, "pd", game_settings_type, f"pd_{id}"),
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
                SrepPD(
                    i,
                    "",
                    os.path.join(log_dir, "pd", game_settings_type, f"pd_{id}"),
                    game_settings,
                )
            )
        elif player_type == "pp":
            players.append(
                PatternPlayer(
                    i,
                    "",
                    os.path.join(log_dir, "pd", game_settings_type, f"pd_{id}"),
                    ["defection", "cooperation"] if "pd" in game_settings_type else ["hare", "stag"],
                )
            )
        elif player_type == "mf":
            players.append(
                MaximizerFreqP(
                    i,
                    "",
                    os.path.join(log_dir, "pd", game_settings_type, f"pd_{id}"),
                    game_settings,
                )
            )
        elif player_type == "tft":
            players.append(
                TftPD(
                    i,
                    "",
                    os.path.join(log_dir, "pd", game_settings_type, f"pd_{id}"),
                    game_settings,
                )
            )

    # create a game object
    game = PrisonersDilemma(
        id,
        players,
        game_settings_type,
        game_settings,
        log_dir,
    )

    # play the game
    game_outcome = game.play(rounds)

    return game_outcome

VALID_PLAYER_TYPES = ["zs", "spp", "cot", "srep", "pp", "mf", "tft"]
VALID_GAMES = ["pd"]
VALID_GAME_SETTINGS = [k for k in PD_SETTINGS_COLLECTION.keys()]

def main2_aux(iteration : int, self_consistency : bool) -> dict[str, list[Thread]]:
    threads : dict[str, list[Thread]] = {}
    for model in models:
        threads_list = list()
        #trial_idx = 200
        for valid_game_setting in VALID_GAME_SETTINGS:
            for player1_type, player2_type in [
                ("zs", "srep"),
                ("zs", "pp"),
                ("zs", "mf"),
                ("zs", "tft"),

                ("spp", "srep"),
                ("spp", "pp"),
                ("spp", "mf"),
                ("spp", "tft"),

                ("cot", "srep"),
                ("cot", "pp"),
                ("cot", "mf"),
                ("cot", "tft"),

                ("zs", "zs"),
                ("zs", "spp"),
                ("zs", "cot"),
                
                ("spp", "zs"),
                ("spp", "spp"),
                ("spp", "cot"),

                ("cot", "zs"),
                ("cot", "spp"),
                ("cot", "cot"),
            ]:
                threads_list.append(
                    Thread(
                        name=f"Thread-{iteration}-{model["id"]}-{valid_game_setting}-{player1_type}-{player2_type}",
                        target=trial_pd,
                        args=(
                            f"{player1_type}_{player2_type}",
                            16,
                            valid_game_setting,
                            PD_SETTINGS_COLLECTION[valid_game_setting],
                            model,
                            1.0,
                            4096,
                            [player1_type, player2_type],
                            [1, 1] if not self_consistency else [3, 1],
                            os.path.join("logs_pd", "logs_3", "data" if not self_consistency else "data_tot", f"iteration_{iteration}"),
                        )
                    )
                )
                #trial_idx += 1
                
                # create directory for the model:
                #log_dir = os.path.join(
                #    "logs_pd",
                #    "logs_3",
                #    "data" if not self_consistency else "data_tot",
                #    f"iteration_{iteration}",
                #    model["name"],
                #    "pd",
                #    valid_game_setting,
                #    f"pd_{player1_type}_{player2_type}"
                #)
                #
                #if self_consistency and os.path.exists(os.path.join(log_dir, "game.json")):
                #    if not os.path.exists(os.path.join(log_dir, "player_10.log")):
                #        # if game.json exists, but player_10.log does not, it means the game was not played
                #        print(f"Problem in {log_dir} because player_10.log does not exist")
#
                #        # clear all the directory files
                #        for file in os.listdir(log_dir):
                #            file_path = os.path.join(log_dir, file)
                #            if os.path.isfile(file_path):
                #                os.remove(file_path)
                #            elif os.path.isdir(file_path):
                #                os.rmdir(file_path)

        threads[model["name"]] = threads_list

    #return threads

def main2_remainder(root_dir: str, rounds: int):
    """
    Find all subdirectories in the given root directory that do not have enough valid games
    """
    threads = dict[str, list[Thread]]()

    import os
    import json
    for root, dirs, _ in os.walk(root_dir):
        for dir in dirs:
            if not dir.startswith("pd_"):
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
                    if len(rounds_played) < rounds:
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

                if model_name in ["Claude Sonnet 4",]:
                    continue

                if model_name not in threads:
                    threads[model_name] = []
                threads[model_name].append(
                    Thread(
                        name=f"Thread-{iteration}-{model_name}-{game_type}-{game_settings_type}-{player_types}",
                        target=trial_pd,
                        args=(
                            f"{player_types[0]}_{player_types[1]}",
                            rounds,
                            game_settings_type,
                            PD_SETTINGS_COLLECTION[game_settings_type],
                            models[[m["name"] for m in models].index(model_name)],
                            1.0,
                            4096,
                            player_types,
                            [1, 1] if not self_consistency else [3, 1],
                            os.path.join("logs_pd", "logs_3", "data" if not self_consistency else "data_tot", f"iteration_{iteration}"),
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
                args=(model_threads, 5)
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
                args=(model_threads, 5)
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
    main2_r(
        "logs_pd/logs_3",
        16,
    )