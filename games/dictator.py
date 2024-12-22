from utils.globals import AgentRole
from games.game import Game

import time
import os

error_msgs = {
    0 : "Messages should begin with [choice].",

    1 : "Do not include any mentions of [choice] \
    after the initial prefix. Please just \
    send a single message, beginning with [choice].",

    2 : "Your message should contain only one choice: 1 or 2.",

    3 : "Your output should begin with [choice].",

}

class DictatorGame(Game):
    def __init__(
        self,
        amount00 : int,
        amount01 : int,
        amount10 : int,
        amount11 : int,
        maximize : bool,
        id : int = int(time.time() * 1_000),
        prompt_path : str = os.path.join("prompts", "dictator.txt"),
        system_prompt_path : str = os.path.join("prompts", "dictator_system.txt"),
        log_path : str = os.path.join("logs", "dictator"),
        MAX_ERRORS=5,
        MAX_MESSAGES=10,
    ):
        super().__init__(id, "dictator", prompt_path, log_path)

        self.MAX_ERRORS = MAX_ERRORS
        self.MAX_MESSAGES = MAX_MESSAGES

        self.amounts = [
            [amount00, amount01],
            [amount10, amount11]
        ]
        self.maximize = maximize

        if self.maximize == True:
            self.act_perf = "maximize"
        else:
            self.act_perf = "minimize"

        self.context = list()

        system_text = None
        with open(self.prompt_path, "r") as f:
            system_text = f.read()

        self.context.append(
            {
                "role": AgentRole.SYSTEM.value,
                "content": self._content_wrapper(
                    system_text.format(
                        amount00=self.amounts[0][0],
                        amount01=self.amounts[0][1],
                        amount10=self.amounts[1][0],
                        amount11=self.amounts[1][1],
                        act_perf=self.act_perf
                    )
                )
            }
        )

        system_text = None
        with open(system_prompt_path, "r") as f:
            system_text = f.read()
        
        self.system_prompt = system_text

        self.log_game = os.path.join(self.log_path, "game.log")
        self.log_agent = os.path.join(self.log_path, "agent_0.log")

        self.messages = list()
        self.game_over = False
        self.proposal : dict[str, int] = None
        self.final_points = None

        self.final_points_logged = False

        # log the initial conditions
        self._log(
            self.log_game,
            "You have two choices:\n\
            1. you receive {amount00} dollars and your partner receives {amount01} dollars.\n\
            2. you receive {amount10} dollars and your partner receives {amount11} dollars.\n\
            \n\
            Your objective is to {act_perf} your money.\n"
            .format(
                amount00=self.amounts[0][0],
                amount01=self.amounts[0][1],
                amount10=self.amounts[1][0],
                amount11=self.amounts[1][1],
                act_perf=self.act_perf
            )
        )

        self._log(self.log_game, "\n\n")

        for _ in range(1):
            self._log(
                self.log_agent,
                "You have two choices:\n\
                1. you receive {amount00} dollars and your partner receives {amount01} dollars.\n\
                2. you receive {amount10} dollars and your partner receives {amount11} dollars.\n\
                \n\
                Your objective is to {act_perf} your money.\n"
                .format(
                    amount00=self.amounts[0][0],
                    amount01=self.amounts[0][1],
                    amount10=self.amounts[1][0],
                    amount11=self.amounts[1][1],
                    act_perf=self.act_perf
                )
            )


    def _validate_response(self, msg : str):
        msg_aux = msg.lower()
        if msg_aux.strip().startswith("[choice]"):
            aux_idx = msg_aux.find("[choice]")

            if aux_idx == -1:
                return False, error_msgs[0]
            
            aux_idx += len("[choice]")
            if "[choice]" in msg_aux[aux_idx:]:
                return False, error_msgs[1]
            
            # Check if the choice is the number 1 or the number 2
            choice_idx1 = msg_aux.find("1")
            choice_idx2 = msg_aux.find("2")

            check_only_one_choice = sum(
                1 for var in [choice_idx1, choice_idx2] if var != -1
            )

            if check_only_one_choice != 1:
                return False, error_msgs[2]
            
            return True, ""
        
        return False, error_msgs[3]

    def _player_response(self):
        response_text = None
        error_cnt = 0
        while True:
            response_text = self._generate_response(
                self.context,
                self.log_agent,
                self.system_prompt,
                1
            )
            is_valid, error_msg = self._validate_response(response_text)
            if is_valid:
                break

            self.context.append(
                {
                    "role": AgentRole.SYSTEM.value,
                    "content": self._content_wrapper(response_text)
                }
            )
            self.context.append(
                {
                    "role" : AgentRole.USER.value,
                    "content" : self._content_wrapper(
                        f"An error occurred. Please resend the previous message \
                        with the following correction, without indicating in any \
                        way that you have made a correction to a prior message: \n \"{error_msg}\" "
                    )
                }
            )

            self._log(
                self.log_agent,
                f"Error: {error_msg}\n"
            )

            error_cnt += 1
            if error_cnt >= self.MAX_ERRORS:
                return "[abort]"
            
        return response_text
        

    def _parse_move(self, msg : str):
        msg_aux = msg.lower()
        choice_idx1 = msg_aux.find("1")
        choice_idx2 = msg_aux.find("2")

        if choice_idx1 != -1:
            return 0
        elif choice_idx2 != -1:
            return 1
        else:
            return None

    def play_game(self):
        while not self.game_over:
            response_text = self._player_response()
            self.messages.append(response_text.strip())

            self._log(
                self.log_game,
                f"Player {0}: {response_text.strip()}",
                newline=True
            )

            if "[abort]" in response_text.strip().lower():
                self.game_over = True

            choice = self._parse_move(response_text)

            self.proposal = {
                "me" : self.amounts[choice][0],
                "partner" : self.amounts[choice][1],
            }

            self.game_over = True

            assistant_message = response_text.strip()

            self.context.append(
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
        return self.proposal is not None

    def _calculate_final_points(self, proposal : dict[str, int]):
        if self.maximize:
            return list(proposal.values())
        else:
            a = -proposal["me"]
            b = -proposal["partner"]
            return [a, b]

    def calculate_final_points(self):
        if not self._is_valid_game():
            self.final_points = [0, 0]
        else:
            self.final_points = self._calculate_final_points(self.proposal)

        if not self.final_points_logged:
            self._log(
                self.log_game,
                f"Player 0 final points: {self.final_points[0]}" +
                f"Player 1 final points: {self.final_points[1]}",
            )
            self.final_points_logged = True

    def is_pareto_optimal(self):
        current_points = self.final_points

        for new_points in self.amounts:
            is_as_good = False
            is_better = False

            if new_points[0] >= current_points[0] and new_points[1] >= current_points[1] :
                is_as_good = True
            if new_points[0] > current_points[0] or new_points[1] > current_points[1]:
                is_better = True

            if is_as_good and is_better:
                return False
        
        # if we don't find a single better allocation of money
        return True