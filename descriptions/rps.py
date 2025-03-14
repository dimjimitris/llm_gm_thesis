RPS_DESC = {
"init":
"""You are playing a game called rock-paper-scissors with other player(s). The game is based on making moves.

Game Description:
There are three possible moves: {rock}, {paper}, and {scissors}.
- {rock} beats {scissors} giving the winner {r} points and the loser -{r} points.
- {paper} beats {rock} giving the winner {p} points and the loser -{p} points.
- {scissors} beats {paper} giving the winner {s} points and the loser -{s} points.
- If both players make the same move, the game is a tie and no points are awarded.

In each round of the game you play against one other player. You and the other player each make a move privately. The moves are compared and you and the other player get your reward/penalty based on the moves made.

Message Formats:
Move messages are sent when you want to make a move.
Move messages are formatted like this:
[move] (Optional explanation here) Your move here

Hint messages are received when you are provided with advice and directions. These messages are important and you should pay attention to them.
Hint messages are formatted like this:
[hint] Hint message here

Objective:
Maximize your points and/or minimize your penalties.

Tips:
- Try to formulate a strategy by reasoning on the provided information.
- Pay attention to the payoff matrix of the game moves.
- You should only send move messages. Hint messages will only be provided to you.
- Pay attention to hints when provided.""",

"game_settings": {
        "eq1" : {
            "r": 1,
            "p": 1,
            "s": 1,
            "move_mapping": {
                "rock": "rock",
                "paper": "paper",
                "scissors": "scissors",
            }
        },
        "eq2" : {
            "r": 2,
            "p": 2,
            "s": 2,
            "move_mapping": {
                "rock": "rock",
                "paper": "paper",
                "scissors": "scissors",
            }
        },
        "r2" : {
            "r": 2,
            "p": 1,
            "s": 1,
            "move_mapping": {
                "rock": "rock",
                "paper": "paper",
                "scissors": "scissors",
            }
        },
        "p2" : {
            "r": 1,
            "p": 2,
            "s": 1,
            "move_mapping": {
                "rock": "rock",
                "paper": "paper",
                "scissors": "scissors",
            }
        },
        "s2" : {
            "r": 1,
            "p": 1,
            "s": 2,
            "move_mapping": {
                "rock": "rock",
                "paper": "paper",
                "scissors": "scissors",
            }
        },
    }

}