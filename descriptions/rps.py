
RPS_INIT_DEFAULT = \
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
- Pay attention to hints when provided.
"""

RPS_INIT_SPP = \
"""You are going to play a game with other player(s). Begin by identifying the personas who could contribute to you winning. Then, initiate a multi-round collaboration process among these personas, until a final decision is reached. The personas will give critical comments and detailed suggestions whenever necessary.

Here is an example on a simpler task from what you will be playing:

---
Example Task 1: Use numbers and basic arithmetic operations (+ - * /) to obtain 24. You need to use all numbers, and each number can only be used once.
Input: 6 12 1 1

Personas: AI Assistant (you); Math Expert

Start collaboration!

Math Expert: Let's analyze the task in detail. You need to make sure that you meet the requirement, that you need to use exactly the four numbers (6 12 1 1) to construct 24. To reach 24, you can think of the common divisors of 24 such as 4, 6, 8, 3 and try to construct these first. Also you need to think of potential additions that can reach 24, such as 12 + 12.
AI Assistant (you): Thanks for the hints! Here's one initial solution: (12 / (1 + 1)) * 6 = 24
Math Expert: Let's check the answer step by step. (1+1) = 2, (12 / 2) = 6, 6 * 6 = 36 which is not 24! The answer is not correct. Can you fix this by considering other combinations? Please do not make similar mistakes.
AI Assistant (you): Thanks for pointing out the mistake. Here is a revised solution considering 24 can also be reached by 3 * 8: (6 + 1 + 1) * (12 / 4) = 24.
Math Expert: Let's first check if the calculation is correct. (6 + 1 + 1) = 8, 12 / 4 = 3, 8 * 3 = 24. The calculation is correct, but you used 6 1 1 12 4 which is not the same as the input 6 12 1 1. Can you avoid using a number that is not part of the input?
AI Assistant (you): You are right, here is a revised solution considering 24 can be reached by 12 + 12 and without using any additional numbers: 6 * (1 - 1) + 12 = 24.
Math Expert: Let's check the answer again. 1 - 1 = 0, 6 * 0 = 0, 0 + 12 = 12. I believe you are very close, here is a hint: try to change the "1 - 1" to "1 + 1".
AI Assistant (you): Sure, here is the corrected answer:  6 * (1+1) + 12 = 24
Math Expert: Let's verify the solution. 1 + 1 = 2, 6 * 2 = 12, 12 + 12 = 12. You used 1 1 6 12 which is identical to the input 6 12 1 1. Everything looks good!

Finish collaboration!

Final decision: 6 * (1 + 1) + 12 = 24

---

Now, the game you will be playing is rock-paper-scissors. Identify the personas and use their multi-round collaboration to help you complete the objective of the the game. You may discuss with your personas on any round of the game, as you see fit.

Game Description:

You are playing a game called rock-paper-scissors with other player(s). The game is based on making moves.

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
- Pay attention to hints when provided.
"""

RPS_GAME_SETTINGS = {
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
    "p5" : {
        "r": 1,
        "p": 5,
        "s": 1,
        "move_mapping": {
            "rock": "rock",
            "paper": "paper",
            "scissors": "scissors",
        }
    },
}