def _calculate_points(
    player_count : int,
    values : list[dict[str, int]],
    player_proposals : list[dict[str, int]],
    objective : str,
    ):

    points = [None, None]

    for id in range(player_count):
        points[id] = 0
        for key, cnt in player_proposals[id].items():
            points[id] += values[id][key] * cnt

    if objective == "semi":
        points = points
    elif objective == "coop":
        points = [points[0] + points[1], points[1] + points[0]]
    elif objective == "comp":
        points = [points[0] - points[1], points[1] - points[0]]
    else:
        raise ValueError("Invalid objective")
        
    return points

def is_pareto_optimal(
    final_points : list[int],
    items : dict[str, int],
    player_count : int,
    values : list[dict[str, int]],
    objective : str,
):
    current_points = final_points

    allocations = [
        [
            {
                "book": bo,
                "hat": ha,
                "ball": ba
            },
            {
                "book": items["book"] - bo,
                "hat": items["hat"] - ha,
                "ball": items["ball"] - ba
            }
        ]
        for bo in range(items["book"] + 1)
        for ha in range(items["hat"] + 1)
        for ba in range(items["ball"] + 1)
    ]

    for player_proposals in allocations:
        is_as_good = False
        is_better = False

        new_points = _calculate_points(
            player_count,
            values,
            player_proposals,
            objective
        )

        if new_points[0] >= current_points[0] and new_points[1] >= current_points[1] :
            is_as_good = True
        if new_points[0] > current_points[0] or new_points[1] > current_points[1]:
            is_better = True

        if is_as_good and is_better:
            return False
    
    # if we don't find a single better allocation of money
    return True