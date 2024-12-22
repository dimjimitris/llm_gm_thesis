from utils.funcs import content_wrapper
from utils.globals import AgentRole
from games.game import Game

import time
import os
import random
import re

error_msgs = {
    0: "Messages should begin with [message].",

    1: "Your output should either begin with [message] or \
    a [propose].",

    2 : "Please begin the dialogue by discussing how you'll \
    divide the items before submitting a private \
    proposal.",

    3 : "Do not include any mentions of [message] or \
    [propose] after the initial prefix. Please just \
    send a single message, beginning with [message].",

    4 : "Opponent's proposal must be followed by a proposal \
    of your own. Please send a proposal, beginning with \
    [propose].",

    5 : "Item counts must be sequenced in the following \
    order: books, hats, and then balls.",

    6 : "There should only be counts for three items in your \
    proposal: books, hats, and balls.",

    7 : "Item counts suggested are invalid based on game \
    context; some of your proposal's item counts are \
    greater than total items available.",

    8 : "Proposals must begin with [propose]. You may resubmit \
    the exact same proposal but with [propose] as a prefix.",
}

class NegotiationGame(Game):
    def _content_wrapper(self, content : str):
        return content_wrapper(content)

    def __init__(
        self,
        item_counts : dict[str, int],
        item_values : list[dict[str, int]],
        objective : str,
        id : int = int(time.time() * 1_000),
        prompt_path : str = os.path.join("prompts", "negotiation.txt"),
        log_path : str = os.path.join("logs", "negotiation"),
    ):
        super().__init__(id, "negotiation", prompt_path, log_path)

        self.item_counts = item_counts
        self.item_values = item_values
        self.objective = objective

        if self.objective == "semi":
            self.obj = "your points"
        elif self.objective == "coop":
            self.obj = "combined points of you and your partner"
        elif self.objective == "comp":
            self.obj = "difference between you and your partner's points"
        else:
            raise ValueError("Invalid objective")
        
        self.contexts = [list(), list()]

        system_text = None
        with open(self.prompt_path, "r") as f:
            system_text = f.read()
        
        for i in range(2):
            self.contexts[i].append(
                {
                    "role": AgentRole.SYSTEM.value,
                    "content": self._content_wrapper(
                        system_text.format(
                            book_cnt=self.item_counts["book"],
                            hat_cnt=self.item_counts["hat"],
                            ball_cnt=self.item_counts["ball"],
                            book_val=self.item_values[i]["book"],
                            hat_val=self.item_values[i]["hat"],
                            ball_val=self.item_values[i]["ball"],
                            obj=self.obj
                        )
                    )
                }
            )

        # create the log paths: one for the game and one for each agent
        self.log_game = os.path.join(self.log_path, "game.log")
        self.log_agents = [
            os.path.join(self.log_path, "agent_0.log"),
            os.path.join(self.log_path, "agent_1.log"),
        ]

        self.messages = list()
        self.game_over = False
        self.deal_proposed = False
        self.proposals : list[dict[str, int]] = [None, None]
        self.final_points = [None, None]

        # a flag to be used in logging final results
        self.final_points_logged = False

        # after the init function is done, we write the initial context to the game log
        self._log(
            self.log_game,
            "Item counts: there are {book_cnt} books, {hat_cnt} hats, and {ball_cnt} balls.\n"
            .format(
                book_cnt=self.item_counts["book"],
                hat_cnt=self.item_counts["hat"],
                ball_cnt=self.item_counts["ball"])
        )
        for i in range(2):
            self._log(
                self.log_game,
                "Player {player_index} values: books are worth {book_val} points, hats are worth {hat_val} points, and balls are worth {ball_val} points.\n"
                .format(
                    player_index=i,
                    book_val=self.item_values[i]["book"],
                    hat_val=self.item_values[i]["hat"],
                    ball_val=self.item_values[i]["ball"]
                )
            )
        self._log(self.log_game, "\n\n")

    def _validate_message(self, msg : str):
        msg = msg.lower()
        aux_idx = msg.find("[message]")
        
        if aux_idx == -1:
            return False, error_msgs[0]

        aux_idx += len("[message]")
        if "[message]" in msg[aux_idx:] or "[propose]" in msg[aux_idx:]:
            return False, error_msgs[3]
        
        if self.deal_proposed:
            return False, error_msgs[4]
        
        return True, ""

    def _validate_proposal(self, msg : str, a_idx : int):
        if len(self.contexts[a_idx]) <= 1:
            return False, error_msgs[2]
        
        if not msg.lower().strip().startswith("[propose]"):
            return False, error_msgs[8]
        
        idx = msg.lower().find("[propose]")
        idx += len("[propose]")
        proposal = msg[idx:].strip()

        # assert that we refer to all of the items and in the correct order
        book_idx = proposal.find("book")
        hat_idx = proposal.find("hat")
        ball_idx = proposal.find("ball")

        # check that we found all indices and they are in the correct order
        if not (-1 < book_idx < hat_idx < ball_idx):
            return False, error_msgs[5]

        # get the quantities as integers (not strings)
        quantities = [int(x) for x in re.findall(r"\d+", proposal)]

        # make sure we have only three integers in our proposal message
        if len(quantities) != 3:
            return False, error_msgs[6]
        
        # make sure the three quantities are within valid range, given the game item counts
        if not (
            0 <= quantities[0] <= self.item_counts["book"]
            and 0 <= quantities[1] <= self.item_counts["hat"]
            and 0 <= quantities[2] <= self.item_counts["ball"]
        ):
            return False, error_msgs[7]
        
        return True, ""

    def _validate_response(self, msg : str, idx : int):
        if msg.lower().strip().startswith("[message]"):
            return self._validate_message(msg)
        elif msg.lower().strip().startswith("[propose]"):
            return self._validate_proposal(msg, idx)
        else:
            return False, error_msgs[1]

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


    def _parse_proposal(self, msg : str):
        # assume it looks like (x, y, z)
        # use regex
        counts = re.findall(r"\d+", msg)
        return {"book": int(counts[0]), "hat": int(counts[1]), "ball": int(counts[2])}


    def play_game(self):

        # a_idx : index of 'assitant' agent
        a_idx = 0 if random.random() < 0.5 else 1
        # u_idx : index of 'user' agent
        u_idx = 1 - a_idx

        # game loops until it's over
        while not self.game_over:
            response_text = self._player_response(a_idx)
            self.messages.append(response_text.strip())

            self._log(
                self.log_game,
                f"Player {a_idx}: {response_text.strip()}",
                newline=True
            )

            # check for abort message
            if "[abort]" in response_text.strip().lower():
                self.game_over = True
                # break

            if response_text.strip().lower().startswith("[propose]"):
                # check if a proposal was already made
                if self.deal_proposed:
                    self.proposals[a_idx] = self._parse_proposal(response_text)
                    self.game_over = True
                else:
                    # first proposal
                    self.proposals[a_idx] = self._parse_proposal(response_text)
                    self.deal_proposed = True
                
                assistant_message = response_text.strip()
                user_message = "[propose] Proposal made. You must now respond with \
                    a proposal of your own. If you've discussed that you should receive \
                    a certain combination of items, this proposal should reflect that. \
                    Keep in mind that you and your partner's proposals should be complementary \
                    - when added, the elementwise sum should exactly equal the total item \
                    counts.\n"
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

            if len(self.messages) >= 50:
                self.game_over = True

            a_idx, u_idx = u_idx, a_idx
        
        # log contexts to the agent logs
        for i in range(2):
            self._log(
                self.log_agents[i],
                str(self.contexts[i])
            )

    def _is_valid_deal(self):
        if self.proposals[0] is None or self.proposals[1] is None:
            return False

        for k, v in self.proposals[0].items():
            if v + self.proposals[1][k] != self.item_counts[k]:
                return False

        return True

    def _calculate_player_points(
        self,
        player_values : dict[str, int],
        proposal_counts : dict[str, int],
    ):
        sum = 0
        for key, cnt in proposal_counts.items():
            sum += cnt * player_values[key]
        
        return sum

    def calculate_final_points(self):
        if not self._is_valid_deal():
            self.final_points = [0, 0]
        else:
            points = [
                self._calculate_player_points(self.item_values[0], self.proposals[0]),
                self._calculate_player_points(self.item_values[1], self.proposals[1]),
            ]
            if self.objective == "semi":
                self.final_points = points
            elif self.objective == "coop":
                self.final_points = [points[0] + points[1], points[1] + points[0]]
            elif self.objective == "comp":
                self.final_points = [points[0] - points[1], points[1] - points[0]]
            else:
                raise ValueError("Invalid objective")
        
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
            {"book": bo, "hat": ha, "ball": ba}
            for bo in range(self.item_counts["book"] + 1)
            for ha in range(self.item_counts["hat"] + 1)
            for ba in range(self.item_counts["ball"] + 1)
        ]

        for alloc in allocations:
            is_as_good = False
            is_better = False

            # decide player counts based on allocation
            p1_cnts = alloc
            p2_cnts = {k: self.item_counts[k] - p1_cnts[k] for k in p1_cnts.keys()}

            # calculate utilities based on allocation
            new_points = [
                self._calculate_player_points(self.item_values[0], p1_cnts),
                self._calculate_player_points(self.item_values[1], p2_cnts),
            ]


            # check if there is a configuration where both players do as good and at least one player does better
            if new_points[0] >= current_points[0] and new_points[1] >= current_points[1] :
                is_as_good = True
            if new_points[0] > current_points[0] or new_points[1] > current_points[1]:
                is_better = True

            if is_as_good and is_better:
                return False

        # if we don't find a single better allocation
        return True
        