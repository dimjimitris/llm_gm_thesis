from utils.negotiation_tools import is_pareto_optimal as is_pareto_optimal_negotiation
from utils.rockpaperscissors_tools import optimal_strategy as optimal_strategy_rockpaperscissors
from utils.dictator_tools import (
    is_pareto_optimal as is_pareto_optimal_dictator,
    dictator_self_best,
)

import os
import numpy as np
import json

def analyze_negotiation(
    path  : str,
    verbose : bool = True,
):
    # collect all scores from both players
    points : list[list] = []
    for i in range(2):
        with open(os.path.join(path,f"agent_{i}_scores"), "r") as f:
            points.append([int(line.strip()) for line in f])
    
    full_points = points[0] + points[1]

    # calculate all scores
    unfiltered_mean = np.mean(full_points)
    unfiltered_median = np.median(full_points)

    # initialize arrays to store indices of games with agreements, token counts, and message count
    agreement_indices = []
    token_counts = []
    message_counts = []

    # track number of aborts
    num_aborts = 0

    # iterate through game indices
    for i in range(len(points[0])):

        # retrieve game json
        json_filename = os.path.join(path, f"negotiation_{i}", "game.json")
        with open(json_filename, "r") as f:
            game_output = json.load(f)

        # check if agreement was reached
        if game_output["is_valid_outcome"]:
            agreement_indices.append(i)

        # append token and message counts
        token_count_aux = 0
        for j in range(2):
            if f"total_tokens_{j}" in game_output:
                token_count_aux += game_output[f"total_tokens_{j}"]
        token_counts.append(token_count_aux)
        message_counts.append(game_output["message_count"])

        # open log file to check for abort messages
        log_filename = os.path.join(path, f"negotiation_{i}", "game.log")
        with open(log_filename, "r") as f:
            text = f.read()

        if "[abort]" in text.lower():
            num_aborts += 1

    # calculate agreement rate
    agreement_points : list[list] = []
    for i in range(len(points)):
        agreement_points.append([points[i][j] for j in agreement_indices])
    agreement_full_points = agreement_points[0] + agreement_points[1]
    proportion_agreement = len(agreement_full_points) / len(full_points)

    # gather total statistics
    total_stats = {
        "mean" : unfiltered_mean,
        "median" : unfiltered_median,
        "length_in_messages" : np.mean(message_counts),
        "length_in_tokens" : np.mean(token_counts) / 2,
        "abort_rate" : num_aborts / len(points[0]),
    }

    if verbose:
        print(f"TOTAL: {total_stats}")

    # agreement stats
    agreement_mean = np.mean(agreement_full_points)
    agreement_median = np.median(agreement_full_points)

    agreement_message_counts = [message_counts[i] for i in agreement_indices]
    agreement_token_counts = [token_counts[i] for i in agreement_indices]

    # calculate proportion of pareto optimal games
    num_optimal = 0
    for i in range(len(points[0])):
        # retrieve game json
        json_filename = os.path.join(path, f"negotiation_{i}", "game.json")
        with open(json_filename, "r") as f:
            game_output = json.load(f)

        try:
            # determine whether game reached pareto-optimality
            is_optimal = is_pareto_optimal_negotiation(
                [
                    game_output[f"player_{j}_points"] for j in range(2)
                ],
                game_output["game_setting"]["items"],
                2,
                game_output["game_setting"]["values"],
                game_output["game_setting"]["objective"],
            )

            if is_optimal:
                num_optimal += 1
        except Exception as e:
            print(f"Error in game {i}: {e}")
            print(game_output)

    # gather agreement statistics
    agreement_stats = {
        "proportion" : proportion_agreement,
        "mean" : agreement_mean,
        "median" : agreement_median,
        "length_in_messages" : np.mean(agreement_message_counts),
        "length_in_tokens" : np.mean(agreement_token_counts) / 2,
        "pareto_optimal_proportion" : num_optimal / len(points[0]),
    }

    if verbose:
        print(f"AGREEMENT: {agreement_stats}")

    # gather statistics for games above average
    cutoff = np.mean(full_points)

    # collect game indices of the games where players scored above average
    above_avg_indices = [list(), list()]
    for i in range(len(points[0])):
        for j in range(2):
            if points[j][i] > cutoff:
                above_avg_indices[j].append(i)

    # collect points for games where players scored above average
    above_avg_points = [[points[j][i] for i in above_avg_indices[j]] for j in range(2)]

    # calculate statistics for games where players scored above average
    above_avg_full_points = above_avg_points[0] + above_avg_points[1]
    above_avg_mean = np.mean(above_avg_full_points)
    above_avg_median = np.median(above_avg_full_points)

    # calculate proportion of games above avg
    proportion_above_avg = len(above_avg_full_points) / len(full_points)

    # extract message/token lengths
    above_avg_message_counts = [
        message_counts[i] for i in above_avg_indices[0] + above_avg_indices[1]
    ]
    above_avg_token_counts = [
        token_counts[i] for i in above_avg_indices[0] + above_avg_indices[1]
    ]

    above_avg_stats = {
        "mean" : above_avg_mean,
        "median" : above_avg_median,
        "length_in_messages" : np.mean(above_avg_message_counts),
        "length_in_tokens" : np.mean(above_avg_token_counts) / 2,
        "proportion" : proportion_above_avg,
    }

    if verbose:
        print(f"ABOVE AVG: {above_avg_stats}")

    return {
        "total" : total_stats,
        "agreement" : agreement_stats,
        "above_avg" : above_avg_stats,
    }

def analyze_rockpaperscissors(
    path : str,
    verbose : bool = True,
):
    # total games played
    num_games = 0
    with open(os.path.join(path, "agent_0_scores"), "r") as f:
        num_games = len([line.strip() for line in f])
    
    # collect rock, paper, scissors frequencies
    frequencies = {
        "rock" : 0,
        "paper" : 0,
        "scissors" : 0,
    }


    # initialize arrays to store indices of games with agreements, token counts, and message count
    agreement_indices = []
    token_counts = []
    message_counts = []

    # track number of aborts
    num_aborts = 0


    # iterate through game indices
    for i in range(num_games):
        # retrieve game json
        json_filename = os.path.join(path, f"rockpaperscissors_{i}", "game.json")
        with open(json_filename, "r") as f:
            game_output = json.load(f)

        # check if agreement was reached
        if game_output["is_valid_outcome"]:
            agreement_indices.append(i)

        # append token and message counts
        token_count_aux = 0
        for j in range(2):
            if f"total_tokens_{j}" in game_output:
                token_count_aux += game_output[f"total_tokens_{j}"]
        token_counts.append(token_count_aux)
        message_counts.append(game_output["message_count"])

        # open log file to check for abort messages
        log_filename = os.path.join(path, f"rockpaperscissors_{i}", "game.log")
        with open(log_filename, "r") as f:
            text = f.read()

        if "[abort]" in text.lower():
            num_aborts += 1

    # gather total statistics
    total_stats = {
        "length_in_messages" : np.mean(message_counts),
        "length_in_tokens" : np.mean(token_counts) / 2,
        "abort_rate" : num_aborts / num_games,
    }

    if verbose:
        print(f"TOTAL: {total_stats}")

    # calculate Nash Equilibrium Strategy
    optimal_frequencies = None

    for i in range(num_games):
        # retrieve game json
        json_filename = os.path.join(path, f"rockpaperscissors_{i}", "game.json")
        with open(json_filename, "r") as f:
            game_output = json.load(f)

        # calculate optimal strategy at the start
        if i == 0:
            optimal_frequencies = optimal_strategy_rockpaperscissors(
                game_output["game_setting"]["p"],
                game_output["game_setting"]["r"],
                game_output["game_setting"]["s"],
            )

        # check if agreement was reached
        if not game_output["is_valid_outcome"]:
            continue

        for j in range(2):
            frequencies[game_output[f"player_{j}_move"]] += 1

    # normalize frequencies
    total = sum(frequencies.values())
    for key in frequencies:
        frequencies[key] /= total

    # calculate error from Nash Equilibrium
    # root mean squared error
    error = 0
    for key in frequencies:
        error += (frequencies[key] - optimal_frequencies[key]) ** 2
    error = np.sqrt(error / len(frequencies))
    
    # gather statistics frequency vs optimal
    frequency_stats = {
        "frequencies" : frequencies,
        "optimal_frequencies" : optimal_frequencies,
        "error" : error,
    }

    if verbose:
        print(f"FREQUENCY: {frequency_stats}")

    return {
        "total" : total_stats,
        "frequency" : frequency_stats,
    }

def analyze_dictator(
    path : str,
    verbose : bool = True,
):
    points : list[list] = []
    for i in range(2):
        with open(os.path.join(path,f"agent_{i}_scores"), "r") as f:
            points.append([int(line.strip()) for line in f])
    
    full_points = points[0] + points[1]

    # calculate all scores
    unfiltered_mean = np.mean(full_points)
    unfiltered_median = np.median(full_points)

    # initialize arrays to store indices of games with agreements, token counts, and message count
    agreement_indices = []
    token_counts = []
    message_counts = []

    # track number of aborts
    num_aborts = 0

    # iterate through game indices
    for i in range(len(points[0])):

        # retrieve game json
        json_filename = os.path.join(path, f"dictator_{i}", "game.json")
        with open(json_filename, "r") as f:
            game_output = json.load(f)

        # check if agreement was reached
        if game_output["is_valid_outcome"]:
            agreement_indices.append(i)

        # append token and message counts
        token_count_aux = 0
        for j in range(1):
            if f"total_tokens_{j}" in game_output:
                token_count_aux += game_output[f"total_tokens_{j}"]
        token_counts.append(token_count_aux)
        message_counts.append(game_output["message_count"])

        # open log file to check for abort messages
        log_filename = os.path.join(path, f"dictator_{i}", "game.log")
        with open(log_filename, "r") as f:
            text = f.read()
        
        if "[abort]" in text.lower():
            num_aborts += 1

    # calculate agreement rate
    agreement_points : list[list] = []
    for i in range(len(points)):
        agreement_points.append([points[i][j] for j in agreement_indices])
    agreement_full_points = agreement_points[0] + agreement_points[1]
    proportion_agreement = len(agreement_full_points) / len(full_points)

    # gather total statistics
    total_stats = {
        "mean" : unfiltered_mean,
        "median" : unfiltered_median,
        "length_in_messages" : np.mean(message_counts),
        "length_in_tokens" : np.mean(token_counts),
        "abort_rate" : num_aborts / len(points[0]),
    }

    if verbose:
        print(f"TOTAL: {total_stats}")

    # agreement stats
    agreement_mean = np.mean(agreement_full_points)
    agreement_median = np.median(agreement_full_points)

    agreement_message_counts = [message_counts[i] for i in agreement_indices]
    agreement_token_counts = [token_counts[i] for i in agreement_indices]

    # calculate proportion of pareto optimal games
    num_optimal = 0
    num_dictator_self_best = 0
    for i in range(len(points[0])):
        # retrieve game json
        json_filename = os.path.join(path, f"dictator_{i}", "game.json")
        with open(json_filename, "r") as f:
            game_output = json.load(f)

        try:
            # determine whether game reached pareto-optimality
            is_optimal = is_pareto_optimal_dictator(
                [
                    game_output[f"player_{j}_points"] for j in range(2)
                ],
                game_output["game_setting"]["amounts"],
                game_output["game_setting"]["objective"],
            )

            if is_optimal:
                num_optimal += 1
            #else:
                #print(f"Game {i} is not pareto optimal")

            # determine whether dictator got the best deal
            is_self_best = dictator_self_best(
                [
                    game_output[f"player_{j}_points"] for j in range(2)
                ],
                game_output["game_setting"]["amounts"],
                game_output["game_setting"]["objective"],
            )

            if is_self_best:
                num_dictator_self_best += 1
            #else:
                #print(f"Game {i} is not dictator self best")
        except Exception as e:
            print(f"Error in game {i}: {e}")
            print(game_output)

    # gather agreement statistics
    agreement_stats = {
        "proportion" : proportion_agreement,
        "mean" : agreement_mean,
        "median" : agreement_median,
        "length_in_messages" : np.mean(agreement_message_counts),
        "length_in_tokens" : np.mean(agreement_token_counts),
        "pareto_optimal_proportion" : num_optimal / len(points[0]),
        "dictator_self_best_proportion" : num_dictator_self_best / len(points[0]),
    }

    if verbose:
        # agreement is when the game is valid...
        print(f"AGREEMENT: {agreement_stats}") 

    return {
        "total" : total_stats,
        "agreement" : agreement_stats,
    }

def main():
    # model names of models we've done experiments on
    model_names = os.listdir("logs")

    # dictator paths
    dictator_paths = [
        {
            "path" : os.path.join("logs", model_name, "dictator"),
            "model_name" : model_name,
        }
        for model_name in model_names
    ]

    # negotiation paths
    negotiation_paths = sum([
        [
            {
                "path" : os.path.join("logs", model_name, "negotiation", game_type),
                "model_name" : model_name,
                "game_type" : game_type,
            }
            for game_type in os.listdir(os.path.join("logs", model_name, "negotiation"))
        ]
        for model_name in model_names
    ], [])

    # rockpaperscissors paths
    rockpaperscissors_paths = sum([
        [
            {
                "path" : os.path.join("logs", model_name, "rockpaperscissors", game_type),
                "model_name" : model_name,
                "game_type" : game_type,
            }
            for game_type in os.listdir(os.path.join("logs", model_name, "rockpaperscissors"))
        ]
        for model_name in model_names
    ], [])

    results = list()

    # analyze dictator games
    for path in dictator_paths:
        result = analyze_dictator(path["path"], False)
        result["model_name"] = path["model_name"]
        result["game"] = "dictator"
        results.append(result)
        print(json.dumps(result, indent=2))
        print()
    
    print("--------------------------------------------------")

    with open(os.path.join("analysis_results", "dictator.json"), "w") as f:
        json.dump(results, f, indent=2)

    results = list()

    # analyze negotiation games
    for path in negotiation_paths:
        result = analyze_negotiation(path["path"], False)
        result["model_name"] = path["model_name"]
        result["game_type"] = path["game_type"]
        result["game"] = "negotiation"
        results.append(result)
        print(json.dumps(result, indent=2))
        print()

    print("--------------------------------------------------")

    with open(os.path.join("analysis_results", "negotiation.json"), "w") as f:
        json.dump(results, f, indent=2)

    results = list()

    # analyze rockpaperscissors games
    for path in rockpaperscissors_paths:
        result = analyze_rockpaperscissors(path["path"], False)
        result["model_name"] = path["model_name"]
        result["game_type"] = path["game_type"]
        result["game"] = "rockpaperscissors"
        results.append(result)
        print(json.dumps(result, indent=2))
        print()

    with open(os.path.join("analysis_results", "rockpaperscissors.json"), "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()