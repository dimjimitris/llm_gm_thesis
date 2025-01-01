from games.game import Game
from utils.globals import AgentRole

import time
import os
import re

class NegotiationGame(Game):
    def __init__(
        self,
        items : dict[str, int],
        values : list[dict[str, int]],
        objective : str,
        model_id : str,
        id : int = int(time.time() * 1_000),
        prompt_path : str = os.path.join("prompts", "negotiation.txt"),
        log_path : str = os.path.join("logs", "negotiation"),
        MAX_ERRORS=5,
        MAX_MESSAGES=30,
        MAX_TOKENS=1_000,
    ):
        super().__init__(
            id,
            "negotiation",
            prompt_path,
            log_path,
            model_id,
            2,
            errors={
                0: "Dialogue messages should begin with [message].",

                1: "Your output should either begin with [message] or a [propose].",

                2 : "Please begin the dialogue by discussing how you'll divide the items before submitting a private proposal.",

                3 : "Your output should either begin with a '[message]' or a '[propose]' and not contain multiple instances of either.",

                4 : "Opponent's proposal must be followed by a proposal of your own. Please send a proposal, beginning with [propose].",

                5 : "Item counts must be sequenced in the following order: books, hats, and then balls.",

                6 : "There should only be counts for three items in your proposal: books, hats, and balls.",

                7 : "Item counts suggested are invalid based on game context; some of your proposal's item counts are greater than total items available.",

                8 : "Proposals must begin with [propose]. You may resubmit the exact same proposal but with [propose] as a prefix.",
            },
            MAX_ERRORS=MAX_ERRORS,
            MAX_MESSAGES=MAX_MESSAGES,
            MAX_TOKENS=MAX_TOKENS,
        )

        self.proposals : list[dict] = [None for _ in range(self.player_count)]

        self.items = items
        self.values = values
        self.objective = objective

        if self.objective == "semi":
            self.obj = "your points"
        elif self.objective == "coop":
            self.obj = "combined points of you and your partner"
        elif self.objective == "comp":
            self.obj = "difference between you and your partner's points"
        else:
            raise ValueError("Invalid objective")
        
        system_text = None
        with open(self.prompt_path, "r") as f:
            system_text = f.read()

        for i in range(self.player_count):
            self.system_prompts.append(
                system_text.format(
                    book_cnt=self.items["book"],
                    hat_cnt=self.items["hat"],
                    ball_cnt=self.items["ball"],
                    book_val=self.values[i]["book"],
                    hat_val=self.values[i]["hat"],
                    ball_val=self.values[i]["ball"],
                    obj=self.obj
                )
            )

        self.contexts[self.first_player].append(
            {
                "role" : AgentRole.USER.value,
                "content" : self._content_wrapper(
                    "[message] Let's play the negotiation game! I will be your partner in the game.\n"
                )
            }
        )

        # log initial setup

        self._log(
            self.log_game,
            "Item counts: there are {book_cnt} books, {hat_cnt} hats, and {ball_cnt} balls.\n"
            .format(
                book_cnt=self.items["book"],
                hat_cnt=self.items["hat"],
                ball_cnt=self.items["ball"]
            )
        )
        for i in range(self.player_count):
            self._log(
                self.log_game,
                "Player {player_index} values: books are worth {book_val} points, hats are worth {hat_val} points, and balls are worth {ball_val} points.\n"
                .format(
                    player_index=i,
                    book_val=self.values[i]["book"],
                    hat_val=self.values[i]["hat"],
                    ball_val=self.values[i]["ball"]
                )
            )
        self._log(self.log_game, "\n\n")

        for i in range(self.player_count):
            self._log(
                self.log_agents[i],
                "Books are worth {book_val} points, hats are worth {hat_val} points, and balls are worth {ball_val} points.\n\n\n"
                .format(
                    book_val=self.values[i]["book"],
                    hat_val=self.values[i]["hat"],
                    ball_val=self.values[i]["ball"]
                )
            )

    def _validate_message(self, msg : str):
        msg = msg.lower()
        aux_idx = msg.find("[message]")
        
        if aux_idx == -1:
            return False, self.errors[0]

        aux_idx += len("[message]")
        if "[message]" in msg[aux_idx:] or "[propose]" in msg[aux_idx:]:
            return False, self.errors[3]
        
        if True in self.moves_made:
            return False, self.errors[4]
        
        return True, ""

    def _validate_proposal(self, msg : str, a_idx : int):
        if len(self.contexts[a_idx]) <= 1:
            return False, self.errors[2]
        
        if not msg.lower().strip().startswith("[propose]"):
            return False, self.errors[8]
        
        idx = msg.lower().find("[propose]")
        idx += len("[propose]")
        proposal = msg[idx:].strip()

        # assert that we refer to all of the items and in the correct order
        book_idx = proposal.find("book")
        hat_idx = proposal.find("hat")
        ball_idx = proposal.find("ball")

        # check that we found all indices and they are in the correct order
        if not (-1 < book_idx < hat_idx < ball_idx):
            return False, self.errors[5]

        # get the quantities as integers (not strings)
        quantities = [int(x) for x in re.findall(r"\d+", proposal)]

        # make sure we have only three integers in our proposal message
        if len(quantities) != 3:
            return False, self.errors[6]
        
        # make sure the three quantities are within valid range, given the game item counts
        if not (
            0 <= quantities[0] <= self.items["book"]
            and 0 <= quantities[1] <= self.items["hat"]
            and 0 <= quantities[2] <= self.items["ball"]
        ):
            return False, self.errors[7]
        
        return True, ""

    def _validate_response(self, msg : str, idx : int):
        if msg.lower().strip().startswith("[message]"):
            return self._validate_message(msg)
        elif msg.lower().strip().startswith("[propose]"):
            return self._validate_proposal(msg, idx)
        else:
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

            is_valid, error_msg = self._validate_response(response_text, idx)
            if is_valid:
                break

            self.contexts[idx].append(
                {
                    "role" : AgentRole.ASSISTANT.value,
                    "content" : self._content_wrapper(
                        response_text
                    )
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
        # assume it looks like (x, y, z)
        # use regex
        counts = re.findall(r"\d+", msg)
        return {"book": int(counts[0]), "hat": int(counts[1]), "ball": int(counts[2])}


    def play_game(self) -> None:
        # a_idx : index of 'assitant' agent
        a_idx = self.first_player
        # u_idx : index of 'user' agent
        u_idx = 1 - a_idx

        # game loops until it's over
        while not self.game_over:
            response_text = self._player_response(a_idx)
            self.messages.append(response_text.strip())

            self._log(
                self.log_game,
                f"Player {a_idx}: {response_text.strip()}\n",
            )

            # check for abort message
            if "[abort]" in response_text.strip().lower():
                self.game_over = True
                # break

            if response_text.strip().lower().startswith("[propose]"):
                # check if a proposal was already made by the other player
                if self.moves_made[u_idx]:
                    self.proposals[a_idx] = self._parse_proposal(response_text)
                    self.moves_made[a_idx] = True
                    self.game_over = True
                else:
                    # first proposal
                    self.proposals[a_idx] = self._parse_proposal(response_text)
                    self.moves_made[a_idx] = True
                
                assistant_message = response_text.strip()
                user_message = "[propose] Proposal made. You must now respond with a proposal of your own. If you've discussed that you should receive a certain combination of items, this proposal should reflect that. Keep in mind that you and your partner's proposals should be complementary - when added, the elementwise sum should exactly equal the total item counts.\n"
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

    def _is_valid_game(self):
        if self.proposals[0] is not None and self.proposals[1] is not None:
            for k, v in self.proposals[0].items():
                if v + self.proposals[1][k] != self.items[k]:
                    return False
            return True
        else:
            return False
    
    def _calculate_points(
        self,
        player_proposals : list[dict[str, int]],
        ):

        points = [None, None]

        for id in range(self.player_count):
            points[id] = 0
            for key, cnt in player_proposals[id].items():
                points[id] += self.values[id][key] * cnt

        if self.objective == "semi":
            points = points
        elif self.objective == "coop":
            points = [points[0] + points[1], points[1] + points[0]]
        elif self.objective == "comp":
            points = [points[0] - points[1], points[1] - points[0]]
        else:
            raise ValueError("Invalid objective")
            
        return points
    
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
                {
                    "book": bo,
                    "hat": ha,
                    "ball": ba
                },
                {
                    "book": self.items["book"] - bo,
                    "hat": self.items["hat"] - ha,
                    "ball": self.items["ball"] - ba
                }
            ]
            for bo in range(self.items["book"] + 1)
            for ha in range(self.items["hat"] + 1)
            for ba in range(self.items["ball"] + 1)
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
    
    def play(self) -> dict[str, any]:
        self.play_game()
        self.calculate_final_points()

        return self._format_game_outcome(
            self.player_count,
            self.final_points,
            self.contexts,
            self._is_valid_game(),
            len(self.messages),
            self.total_tokens,
        )