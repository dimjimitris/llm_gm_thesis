from games.game import Game
from utils.globals import AgentRole

import time
import os
from tabulate import tabulate
import json

class RockPaperScissorsGame(Game):
    def __init__(
        self,
        paper_beats_rock : int,
        rock_beats_scissors : int,
        scissors_beats_paper : int,
        tie : int,
        model_id : str,
        id : int = int(time.time() * 1_000),
        prompt_path : str = os.path.join("prompts", "rockpaperscissors.txt"),
        log_path : str = os.path.join("logs", "rockpaperscissors"),
        MAX_ERRORS=5,
        MAX_MESSAGES=10,
        MAX_TOKENS=1_000,
    ):
        super().__init__(
            id,
            "rockpaperscissors",
            prompt_path,
            log_path,
            model_id,
            2,
            errors={
                0 : "Your output should begin with [move] or [message].",

                1 : "Dialogue messages should begin with [message].",

                2 : "Your output should either begin with [move] or a [message] and not contain multiple instances of either.",

                3 : "Opponent's move must be followed by a move of your own. Please send a move, beginning with [move].",

                4 : "Your move must begin with [move] and must be followed by one of 'rock', 'paper', or 'scissors'.",

                5 : "Your move message must begin with [move].",
            },
            MAX_ERRORS=MAX_ERRORS,
            MAX_MESSAGES=MAX_MESSAGES,
            MAX_TOKENS=MAX_TOKENS,
        )
        
        self.p = paper_beats_rock
        self.r = rock_beats_scissors
        self.s = scissors_beats_paper
        self.tie = tie

        system_text = None
        with open(self.prompt_path, "r") as f:
            system_text = f.read()

        for _ in range(self.player_count):
            self.system_prompts.append(
                system_text.format(
                    p=self.p,
                    r=self.r,
                    s=self.s,
                    tie=self.tie
                )
            )

        self.contexts[self.first_player].append(
            {
                "role" : AgentRole.USER.value,
                "content" : self._content_wrapper(
                    "[message] Let's play rock-paper-scissors! I will be your partner in the game. Please make your move.\n"
                )
            }
        )

        payoff_matrix_str = \
            tabulate(
                tabular_data=[
                    ["rock", (self.tie, self.tie), (-self.p, self.p), (self.r, -self.r)],
                    ["paper", (self.p, -self.p), (self.tie, self.tie), (-self.s, self.s)],
                    ["scissors", (-self.r, self.r), (self.s, -self.s), (self.tie, self.tie)]
                ],
                headers=["", "rock", "paper", "scissors"],
                tablefmt="github"
            )

        self._log(
            self.log_game,
            payoff_matrix_str,
            mode="a",
            trail="\n\n\n"
        )

        for i in range(2):
            self._log(
                self.log_agents[i],
                payoff_matrix_str,
                mode="a",
                trail="\n\n\n"
            )

    def _validate_message(self, msg : str):
        msg = msg.lower()
        aux_idx = msg.find("[message]")

        if aux_idx == -1:
            return False, self.errors[1]
        
        aux_idx += len("[message]")
        if "[message]" in msg[aux_idx:] or "[move]" in msg[aux_idx:]:
            return False, self.errors[2]
        
        if True in self.moves_made:
            return False, self.errors[3]

        return True, ""

    def _validate_move(self, msg : str):
        msg_aux = msg.lower()
        if msg_aux.strip().startswith("[move]"):

            move = msg_aux.split()[1].strip()

            if move not in ["rock", "paper", "scissors"]:
                return False, self.errors[4]
            
            return True, ""
        else:
            return False, self.errors[5]

    def _validate_response(self, msg : str, idx : int):
        if msg.lower().strip().startswith("[message]"):
            return self._validate_message(msg)
        elif msg.lower().strip().startswith("[move]"):
            return self._validate_move(msg)
        else:
            return False, self.errors[0]
            

    def _player_response(self, idx : int):
        response_text = None
        error_cnt = 0
        while True:
            response_obj = self._generate_response(
                self.contexts[idx],
                self.log_agents[idx],
                self.system_prompts[idx],
            )

            response_text = response_obj["output_text"]
            self.total_tokens[idx] = response_obj["total_tokens"]

            is_valid, error_msg = self._validate_response(response_text, idx)
            if is_valid:
                break

            self.contexts[idx].append(
                {
                    "role": AgentRole.ASSISTANT.value,
                    "content": self._content_wrapper(response_text)
                }
            )
            self.contexts[idx].append(
                {
                    "role" : AgentRole.USER.value,
                    "content" : self._content_wrapper(
                        f"An error occurred. Please resend the previous message with the following correction, without indicating in any way that you have made a correction to a prior message: \n \"{error_msg}\" "
                    )
                }
            )

            self._log(
                self.log_agents[idx],
                f"Error: {error_msg}\n"
            )

            error_cnt += 1
            if error_cnt >= self.MAX_ERRORS:
                return "[abort]"
            
        return response_text

    def _parse_proposal(self, msg : str):
        msg_aux = msg.lower()

        move = msg_aux.split()[1].strip()

        if move in ["rock", "paper", "scissors"]:
            return move
        else:
            return None

    def play_game(self):
        # a_idx : index of 'assitant' agent
        a_idx = self.first_player
        # u_idx : index of 'user' agent
        u_idx = 1 - a_idx

        while not self.game_over:
            response_text = self._player_response(a_idx)
            self.messages.append(response_text.strip())

            self._log(
                self.log_game,
                f"Player {a_idx}: {response_text.strip()}\n"
            )

            if "[abort]" in response_text.strip().lower():
                self.game_over = True

            if response_text.strip().lower().startswith("[move]"):
                # check if move has already been made by the other player
                if self.moves_made[u_idx]:
                    self.proposals[a_idx] = self._parse_proposal(response_text)
                    self.moves_made[a_idx] = True
                    self.game_over = True
                else:
                    # first move
                    self.proposals[a_idx] = self._parse_proposal(response_text)
                    self.moves_made[a_idx] = True

                assistant_message = response_text.strip()
                user_message = "[move] Move made. You must now respond with a move of your own. \n"
                
            else:
                # update prompts of each player normally, since this is a regular message
                assistant_message = response_text.strip()
                user_message = response_text.strip()

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

            if len(self.messages) >= self.MAX_MESSAGES:
                self.game_over = True

            a_idx, u_idx = u_idx, a_idx

        #for i in range(2):
        #    self._log(
        #        self.log_agents[i],
        #        str(self.contexts[i])
        #    )
            
    def _is_valid_game(self):
        return self.proposals[0] is not None and self.proposals[1] is not None

    def _calculate_points(self, player_proposals):
        move1 = player_proposals[0]
        move2 = player_proposals[1]

        if move1 == "rock" and move2 == "rock":
            return [self.tie, self.tie]
        elif move1 == "rock" and move2 == "paper":
            return [-self.p, self.p]
        elif move1 == "rock" and move2 == "scissors":
            return [self.r, -self.r]
        elif move1 == "paper" and move2 == "rock":
            return [self.p, -self.p]
        elif move1 == "paper" and move2 == "paper":
            return [self.tie, self.tie]
        elif move1 == "paper" and move2 == "scissors":
            return [-self.s, self.s]
        elif move1 == "scissors" and move2 == "rock":
            return [-self.r, self.r]
        elif move1 == "scissors" and move2 == "paper":
            return [self.s, -self.s]
        elif move1 == "scissors" and move2 == "scissors":
            return [self.tie, self.tie]
        else:
            raise ValueError("Invalid move. Moves must be 'rock', 'paper', or 'scissors'.")

    def calculate_final_points(self):
        if not self._is_valid_game():
            self.final_points = [self.tie, self.tie]
        else:
            self.final_points = self._calculate_points(self.proposals)

        if not self.final_points_logged:
            self._log(
                self.log_game,
                f"Player 0 final points: {self.final_points[0]}\n" +
                f"Player 1 final points: {self.final_points[1]}\n",
            )
            self.final_points_logged = True

    def is_pareto_optimal(self):
        current_points = self.final_points

        allocations = [
            [move1, move2]
            for move1 in ["rock", "paper", "scissors"]
            for move2 in ["rock", "paper", "scissors"]
        ]

        for player_proposals in allocations:
            is_as_good = False
            is_better = False

            new_points = self._calculate_points(player_proposals)

            if new_points[0] >= current_points[0] and new_points[1] >= current_points[1] :
                is_as_good = True
            if new_points[0] > current_points[0] or new_points[1] > current_points[1]:
                is_better = True

            if is_as_good and is_better:
                return False
            
        return True

    def play(self) -> dict[str, any]:
        self.play_game()
        self.calculate_final_points()

        # log player json files
        for i in range(self.player_count):
            with open(self.json_agents[i], "w") as f:
                json.dump(self.contexts[i], f, indent=2)

        game_json = self._format_game_outcome(
            self.player_count,
            self.final_points,
            self.contexts,
            self._is_valid_game(),
            len(self.messages),
            self.total_tokens,
            self.proposals,
        )
    
        # log game json file
        with open(self.json_game, "w") as f:
            json.dump(game_json, f, indent=2)

        # add game setting to game json
        game_json["game_setting"] = {
            "p" : self.p,
            "r" : self.r,
            "s" : self.s,
            "tie" : self.tie
        }

        return game_json