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
    #{
    #    "id" : "us.anthropic.claude-sonnet-4-20250514-v1:0",
    #    "name" : "Claude Sonnet 4",
    #    "thinking" : False,
    #},
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
    #{
    #    "id" : "mistral.mistral-large-2407-v1:0",
    #    "name" : "Mistral Large (24.07)",
    #    "thinking" : False,
    #},
    #{
    #    "id" : "us.deepseek.r1-v1:0",
    #    "name" : "DeepSeek-R1",
    #    "thinking" : False,
    #},
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

        threads[model["name"]] = threads_list

    return threads

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
    main2(2, True)