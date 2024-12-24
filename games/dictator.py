from utils.globals import AgentRole
from games.game import Game

import time
import os


class DictatorGame(Game):
    def __init__(
        self,
        amounts : list[list[int]],
        objective : str,
        model_id : str,
        id : int = int(time.time() * 1_000),
        prompt_path : str = os.path.join("prompts", "dictator.txt"),
        log_path : str = os.path.join("logs", "dictator"),
        MAX_ERRORS=5,
        MAX_MESSAGES=10,
        MAX_TOKENS=1_000,
    ):
        super().__init__(
            id,
            "dictator",
            prompt_path,
            log_path,
            model_id,
            1,
            errors={
                0 : "Your choice must begin with [choice] and must be followed by 1 or 2.",

                1 : "Your choice message must begin with [choice].",
            },
            MAX_ERRORS=MAX_ERRORS,
            MAX_MESSAGES=MAX_MESSAGES,
            MAX_TOKENS=MAX_TOKENS,
        )

        self.proposals : list[dict] = [None for _ in range(self.player_count)]

        self.amounts = amounts
        self.objective = objective

        system_text = None
        with open(self.prompt_path, "r") as f:
            system_text = f.read()

        for _ in range(self.player_count):
            self.system_prompts.append(
                system_text.format(
                    amount00=self.amounts[0][0],
                    amount01=self.amounts[0][1],
                    amount10=self.amounts[1][0],
                    amount11=self.amounts[1][1],
                    act_perf=self.objective
                )
            )
        
        self.contexts[self.first_player].append(
            {
                "role" : AgentRole.USER.value,
                "content" : self._content_wrapper(
                    "[message] Let's play the dictator game! I will be your partner in the game.\n"
                )
            }
        )

        self._log(
            self.log_game,
            "You have two choices:\n1. you receive {amount00} dollars and your partner receives {amount01} dollars.\n2. you receive {amount10} dollars and your partner receives {amount11} dollars.\n\nYour objective is to {act_perf} your money.\n"
            .format(
                amount00=self.amounts[0][0],
                amount01=self.amounts[0][1],
                amount10=self.amounts[1][0],
                amount11=self.amounts[1][1],
                act_perf=self.objective
            ),
            mode="a",
            trail="\n\n"
        )

        for i in range(1):
            self._log(
                self.log_agents[i],
                "You have two choices:\n1. you receive {amount00} dollars and your partner receives {amount01} dollars.\n2. you receive {amount10} dollars and your partner receives {amount11} dollars.\n\nYour objective is to {act_perf} your money.\n"
                .format(
                    amount00=self.amounts[0][0],
                    amount01=self.amounts[0][1],
                    amount10=self.amounts[1][0],
                    amount11=self.amounts[1][1],
                    act_perf=self.objective
                ),
                mode="a",
                trail="\n\n"
            )


    def _validate_response(self, msg : str):
        msg_aux = msg.lower()
        if msg_aux.strip().startswith("[choice]"):
            
            move = msg_aux.split()[1].strip()
            if move not in ["1", "2"]:
                return False, self.errors[0]
            
            return True, ""
        
        return False, self.errors[1]

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

            is_valid, error_msg = self._validate_response(response_text)
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

        if move in ["1", "2"]:
            return int(move) - 1
        else:
            return None

    def play_game(self):
        a_idx = self.first_player

        while not self.game_over:
            response_text = self._player_response(a_idx)
            self.messages.append(response_text.strip())

            self._log(
                self.log_game,
                f"Player {0}: {response_text.strip()}\n",
            )

            if "[abort]" in response_text.strip().lower():
                self.game_over = True

            choice = self._parse_proposal(response_text)

            self.proposals[a_idx] = {
                "me" : self.amounts[choice][0],
                "partner" : self.amounts[choice][1],
            }

            self.game_over = True

            assistant_message = response_text.strip()

            self.contexts[a_idx].append(
                {
                    "role" : AgentRole.ASSISTANT.value,
                    "content" : self._content_wrapper(assistant_message)
                }
            )

            if len(self.messages) >= self.MAX_MESSAGES:
                self.game_over = True

        #for _ in range(1):
        #    self._log(
        #        self.log_agent,
        #        str(self.context),
        #    )

    def _is_valid_game(self):
        return self.proposals[0] is not None

    def _calculate_points(self, player_proposals : list[dict[str, int]]):
        proposal = player_proposals[self.first_player]
        
        me = proposal["me"]
        partner = proposal["partner"]

        if self.objective == "maximize":
            return [me, partner]
        elif self.objective == "minimize":
            return [-me, -partner]
        else:
            raise ValueError("Invalid objective")

    def calculate_final_points(self):
        if not self._is_valid_game():
            self.final_points = [0, 0]
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
            [
                {"me" : self.amounts[choice][0], "partner" : self.amounts[choice][1]}
            ]
            for choice in range(2)
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
        
        # if we don't find a single better allocation of money
        return True
    
    def play(self):
        self.play_game()
        self.calculate_final_points()

        output = self._format_game_outcome(
            self.player_count,
            self.final_points,
            self.contexts,
            self._is_valid_game(),
            len(self.messages),
            self.total_tokens,
        )

        output["player_1_points"] = self.final_points[1]

        return output