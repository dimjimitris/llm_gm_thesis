from utils.funcs import content_wrapper
from utils.globals import AgentRole
from games.game import Game

import time
import os
from tabulate import tabulate
import random

error_msgs = {
    0 : "Messages should begin with [move].",

    1 : "Do not include any mentions of [move] \
    after the initial prefix. Please just \
    send a single message, beginning with [move].",

    2 : "Your message should contain only one move: rock, paper, or scissors.",

    3 : "Your output should begin with [move].",
}

class RockPaperScissorsGame(Game):
    def _content_wrapper(self, content : str):
        return content_wrapper(content)

    def __init__(
        self,
        paper_beats_rock,
        rock_beats_scissors,
        scissors_beat_paper,
        tie,
        id : int = int(time.time() * 1_000),
        prompt_path : str = os.path.join("prompts", "rockpaperscissors.txt"),
        log_path : str = os.path.join("logs", "rockpaperscissors"),
    ):
        super().__init__(id, "rockpaperscissors", prompt_path, log_path)

        self.p = paper_beats_rock
        self.r = rock_beats_scissors
        self.s = scissors_beat_paper
        self.tie = tie

        self.contexts = [list(), list()]

        system_text = None
        with open("prompts/rockpaperscissors.txt", "r") as f:
            system_text = f.read()

        for i in range(2):
            self.contexts[i].append(
                {
                    "role": AgentRole.SYSTEM.value,
                    "content": self._content_wrapper(
                        system_text.format(
                            p=self.p,
                            r=self.r,
                            s=self.s,
                            tie=self.tie
                        )
                    )
                }
            )

        self.log_game = os.path.join(self.log_path, "game.log")
        self.log_agents =[
            os.path.join(self.log_path, "agent_0.log"),
            os.path.join(self.log_path, "agent_1.log")
        ]

        self.messages = list()
        self.game_over = False
        self.move_made = False
        self.moves : list[str] = [None, None]
        self.final_points = [None, None]

        self.final_points_logged = False

        self._log(
            self.log_game,
            tabulate(
                tabular_data=[
                    ["rock", (self.tie, self.tie), (-self.p, self.p), (self.r, -self.r)],
                    ["paper", (self.p, -self.p), (self.tie, self.tie), (-self.s, self.s)],
                    ["scissors", (-self.r, self.r), (self.s, -self.s), (self.tie, self.tie)]
                ],
                headers=["", "rock", "paper", "scissors"],
                tablefmt="github"
            )
        )

        self._log(self.log_game, "\n\n")

    def _validate_response(self, msg : str, idx : int):
        msg_aux = msg.lower()
        if msg_aux.strip().startswith("[move]"):

            aux_idx = msg_aux.find("[move]")
            
            if aux_idx == -1:
                return False, error_msgs[0]
            
            aux_idx += len("[move]")
            if "[move]" in msg_aux[aux_idx:]:
                return False, error_msgs[1]
            
            rock_idx = msg_aux.find("rock")
            paper_idx = msg_aux.find("paper")
            scissors_idx = msg_aux.find("scissors")

            check_only_one_move = sum(
                1 for var in [rock_idx, paper_idx, scissors_idx] if var != -1
            )

            if check_only_one_move != 1:
                return False, error_msgs[2]
            
            return True, ""
        else:
            return False, error_msgs[3]

        
            

    def _player_response(self, idx : int):
        response_text = None
        error_cnt = 0
        while True:
            response_text = "placeholder"
            is_valid, error_msg = self._validate_response(response_text, idx)
            if is_valid:
                break

            self.contexts[idx].append(
                {
                    "role": AgentRole.SYSTEM.value,
                    "content": self._content_wrapper(response_text)
                }
            )
            self.contexts[idx].append(
                {
                    "role" : AgentRole.USER.value,
                    "content" : self._content_wrapper(
                        f"An error occurred. Please resend the previous message \
                        with the following correction, without indicating in any \
                        way that you have made a correction to a prior message: \n \"{error_msg}\" "
                    )
                }
            )

            error_cnt += 1
            if error_cnt > 4:
                return "[abort]"
            
        return response_text

    def _parse_move(self, msg : str):
        msg_aux = msg.lower()
        if "rock" in msg_aux:
            return "rock"
        elif "paper" in msg_aux:
            return "paper"
        elif "scissors" in msg_aux:
            return "scissors"
        else:
            return None

    def play_game(self):
        # a_idx : index of 'assitant' agent
        a_idx = 0 if random.random() < 0.5 else 1
        # u_idx : index of 'user' agent
        u_idx = 1 - a_idx

        while not self.game_over:
            response_text = self._player_response(a_idx)
            self.messages.append(response_text.strip())

            self._log(
                self.log_game,
                f"Player {a_idx}: {response_text.strip()}",
                newline=True
            )

            if "[abort]" in response_text.strip().lower():
                self.game_over = True

            # check if move has already been made
            if self.move_made:
                self.moves[a_idx] = self._parse_move(response_text)
                self.game_over = True
            else:
                # first move
                self.moves[a_idx] = self._parse_move(response_text)
                self.move_made = True

            assistant_message = response_text.strip()
            user_message = "[move] Move made. You must now respond with \
                a move of your own. \n"
            
            self.contexts[a_idx].append(
                {
                    "role" : AgentRole.ASSISTANT.value,
                    "content" : self._content_wrapper(
                        assistant_message
                    )
                }
            )
            self.contexts[u_idx].append(
                {
                    "role" : AgentRole.USER.value,
                    "content" : self._content_wrapper(
                        user_message
                    )
                }
            )

            if len(self.messages) >= 10:
                self.game_over = True

            a_idx, u_idx = u_idx, a_idx

        for i in range(2):
            self._log(
                self.log_agents[i],
                str(self.contexts[i])
            )
            
    def _is_valid_game(self):
        return self.moves[0] is not None and self.moves[1] is not None

    def _calculate_player_points(self, move1, move2):
        if move1 == "rock" and move2 == "rock":
            return self.tie
        elif move1 == "rock" and move2 == "paper":
            return -self.p
        elif move1 == "rock" and move2 == "scissors":
            return self.r
        elif move1 == "paper" and move2 == "rock":
            return self.p
        elif move1 == "paper" and move2 == "paper":
            return self.tie
        elif move1 == "paper" and move2 == "scissors":
            return -self.s
        elif move1 == "scissors" and move2 == "rock":
            return -self.r
        elif move1 == "scissors" and move2 == "paper":
            return self.s
        elif move1 == "scissors" and move2 == "scissors":
            return self.tie
        else:
            raise ValueError("Invalid move. Moves must be 'rock', 'paper', or 'scissors'.")

    def calculate_final_points(self):
        if not self._is_valid_game():
            self.final_points = [self.tie, self.tie]
        else:
            self.final_points = [
                self._calculate_player_points(self.moves[0], self.moves[1]),
                self._calculate_player_points(self.moves[1], self.moves[0])
            ]

        if not self.final_points_logged:
            self._log(
                self.log_game,
                f"Player 0 final points: {self.final_points[0]}\n" +
                f"Player 1 final points: {self.final_points[1]}\n"
            )
            self.final_points_logged = True