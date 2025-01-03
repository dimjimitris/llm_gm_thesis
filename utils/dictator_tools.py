def _calculate_points(
        first_player : int,
        player_proposals : list[dict[str, int]],
        objective : str,
    ):

    proposal = player_proposals[first_player]
    
    me = proposal["me"]
    partner = proposal["partner"]

    if objective == "maximize":
        return [me, partner]
    elif objective == "minimize":
        return [-me, -partner]
    else:
        raise ValueError("Invalid objective")

def is_pareto_optimal(
    final_points : list[int],
    amounts : list[list[int]],
    objective : str,
    ):
    current_points = final_points

    allocations = [
        [
            {"me" : amounts[choice][0], "partner" : amounts[choice][1]}
        ]
        for choice in range(2)
    ]

    for player_proposals in allocations:
        is_as_good = False
        is_better = False

        new_points = _calculate_points(
            0,
            player_proposals,
            objective,
        )

        if new_points[0] >= current_points[0] and new_points[1] >= current_points[1] :
            is_as_good = True
        if new_points[0] > current_points[0] or new_points[1] > current_points[1]:
            is_better = True

        if is_as_good and is_better:
            return False
    
    # if we don't find a single better allocation of money
    return True

def dictator_self_best(
    final_points : list[int],
    amounts : list[list[int]],
    objective : str,
    ):
    current_points = final_points

    allocations = [
        [
            {"me" : amounts[choice][0], "partner" : amounts[choice][1]}
        ]
        for choice in range(2)
    ]

    for player_proposals in allocations:
        is_as_good = False
        is_better = False

        new_points = _calculate_points(
            0,
            player_proposals,
            objective,
        )

        # 0 is always the dictator
        if new_points[0] >= current_points[0] :
            is_as_good = True
        if new_points[0] > current_points[0]:
            is_better = True

        if is_as_good and is_better:
            return False
    
    # if we don't find a single better allocation of money
    return True

