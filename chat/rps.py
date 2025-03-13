from chat.bedrock import (
    Player,
    BedrockChat,
)

from prompts.rps import (
    RPS_PROMPTS,
)

from utils.globals import (
    PlayerRole,
)

from utils.rps import (
    optimal_strategy,
)

INITIAL_PROMPT = RPS_PROMPTS["initial"]

import random
import tabulate
import json
import statistics
from collections import Counter

class RockPaperScissorsGame(BedrockChat):
    """
    Parameterized Rock-Paper-Scissors game. Allows for easy creation of counterfactual RPS games.

    Attributes
    ----------
    id : int
        game id
    game_type : str
        type of the game, e.g., "rps"
    unique_name : str
        unique name for the game, should be {game_type}_{id}
    game_log : str
        path to the game's log file
    info_log : str
        path to the game's info file
    temp : float
        temperature parameter for sampling
    max_tokens : int
        maximum number of tokens to generate
    model_id : str
        bedrock model id
    players : list
        list of player objects, should have two players
    r : int
        reward for rock beating scissors
    p : int
        reward for paper beating rock
    s : int
        reward for scissors beating paper
    move_mapping : dict
        mapping of moves to moves
    system_prompt : str
        initial system prompt to start the game
    first_player_idx : int
        index of the first player to play
    total_tokens : list
        list of total tokens generated
    """
    def __init__(
        self,
        id: int,
        log_path: str,
        temp: float,
        max_tokens: int,
        model_id: str,
        rock_beats_scissors: int,
        paper_beats_rock: int,
        scissors_beats_paper: int,
        move_mapping: dict = {
            "rock": "rock",
            "paper": "paper",
            "scissors": "scissors",
        },
    ):
        """
        Parameters
        ----------
        id : int
            game id
        log_path : str
            path to the root log directory
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        model_id : str
            bedrock model id
        rock_beats_scissors : int
            reward for rock beating scissors
        paper_beats_rock : int
            reward for paper beating rock
        scissors_beats_paper : int
            reward for scissors beating paper
        move_mapping : dict
            mapping of moves to moves
        """
        super().__init__(
            id=id,
            game_type="rps",
            log_path=log_path,
            temp=temp,
            max_tokens=max_tokens,
            model_id=model_id,
        )
        self.r = rock_beats_scissors
        self.p = paper_beats_rock
        self.s = scissors_beats_paper
        self.move_mapping = move_mapping

        self.system_prompt = INITIAL_PROMPT.format(
            rock=self.move_mapping["rock"],
            paper=self.move_mapping["paper"],
            scissors=self.move_mapping["scissors"],
            r=self.r,
            p=self.p,
            s=self.s,
        )
        self.first_player_idx = -1
        self.total_tokens = list()

    def add_players(
        self,
        player1 : Player,
        player2 : Player,
        rand_player_seq : bool =True,
    ):
        """
        Parameters
        ----------
        player1 : Player
            player object, refers to player_0
        player2 : Player
            player object, refers to player_1
        rand_player_seq : bool
            whether to randomize the player sequence or not. If False, player_0 goes first, otherwise randomize
        """
        self.players = [player1, player2]
        self.first_player_idx = random.choice([0, int(rand_player_seq)])

    def play_round(self) -> list[str]:
        """
        Play a round of the game

        Returns
        -------
        list[str]
            list of moves made by the players
        """
        curr_player_idx = self.first_player_idx
        other_player_idx = 1 - curr_player_idx
        curr_player = self.players[curr_player_idx]
        other_player = self.players[other_player_idx]
        self.total_tokens.append([0, 0])

        if other_player.active:
            curr_player.append_context({
                "role": PlayerRole.USER.value,
                "content": self._content_wrapper(
                    "[hint] Let's play another round. Please make your move.\n"
                )
            })
        else:
            if other_player.fresh:
                curr_player.append_context({
                    "role": PlayerRole.USER.value,
                    "content": self._content_wrapper(
                        "[hint] Let's play rock-paper-scissors. You are playing against a fresh player. Please make your move.\n"
                    )
                })
            else:
                curr_player.append_context({
                    "role": PlayerRole.USER.value,
                    "content": self._content_wrapper(
                        "[hint] Let's play rock-paper-scissors. You are playing against an experienced player. Please make your move.\n"
                    )
                })

        round_over = False
        moves_made = [None, None]
        while not round_over:
            response_text, tokens = self._player_response(curr_player)
            self.total_tokens[-1][curr_player_idx] += tokens

            if "[abort]" in response_text:
                round_over = True
            
            if response_text.startswith("[move]"):
                moves_made[curr_player_idx] = self._parse_move(response_text)
                round_over = moves_made[other_player_idx] is not None
                
                assistant_msg = response_text
                user_msg = "[hint] Move made by the other player. You must now respond with a move of your own.\n"
            else:
                assistant_msg = response_text
                user_msg = response_text

            curr_player.append_context({
                "role": PlayerRole.ASSISTANT.value,
                "content": self._content_wrapper(assistant_msg)
            })
            other_player.append_context({
                "role": PlayerRole.USER.value,
                "content": self._content_wrapper(user_msg)
            })

            curr_player_idx, other_player_idx = other_player_idx, curr_player_idx
            curr_player = self.players[curr_player_idx]
            other_player = self.players[other_player_idx]

        curr_player.active = True
        other_player.active = True

        return moves_made

    def _player_response(
        self,
        player : Player,
    ) -> tuple[str, int]:
        tokens = 0
        response_text = None
        error_cnt = 0
        while True:
            response_obj = self._generate_response(player)
            response_text : str = response_obj["output_text"]
            if not response_text.endswith("\n"):
                response_text += "\n"

            tokens += response_obj["total_tokens"]

            is_valid, error_msg = self._validate_response(response_text)
            if is_valid:
                break

            player.append_context({
                "role": PlayerRole.ASSISTANT.value,
                "content": self._content_wrapper(response_text)
            })
            player.append_context({
                "role": PlayerRole.USER.value,
                "content": self._content_wrapper(
                    f"An error occurred. Please resend the previous message with the following correction, without indicating in any way that you have made a correction to a prior message: \n \"{error_msg}\"\n"
                )
            })

            error_cnt += 1
            if error_cnt >= 5:
                return "[abort]\n", tokens
            
        return response_text, tokens

    def _validate_response(self, msg : str) -> tuple[bool, str]:
        """
        Validate the response message

        Parameters
        ----------
        msg : str
            response message

        Returns
        -------
        tuple[bool, str]
            whether the message is valid and an error message if not
        """
        if msg.startswith("[move]"):
            return self._validate_move(msg)
        
        return False, "Your output should be a move message. Move messages begin with the tag [move] and end with a valid move: 'rock', 'paper', or 'scissors'."
    
    def _validate_move(self, msg : str) -> tuple[bool, str]:
        """
        Validate the move message

        Parameters
        ----------
        msg : str
            move message

        Returns
        -------
        tuple[bool, str]
            whether the message is valid and an error message if not
        """
        msg_aux = msg.lower().strip()
        # move should be the last word in the message
        move = msg_aux.split()[-1]
        if move not in self.move_mapping.values():
            return False, "Your move must begin with the tag [move] and end with a valid move: 'rock', 'paper', or 'scissors'."
        
        return True, ""
    
    def _parse_move(self, msg : str) -> str:
        """
        Parse the move message

        Parameters
        ----------
        msg : str
            move message

        Returns
        -------
        str
            move made by the player
        """
        return msg.lower().strip().split()[-1]
    
    def _calculate_points(self, moves_made : list[str]) -> tuple[int, int]:
        """
        Calculate the points for the players

        Parameters
        ----------
        moves_made : list[str]
            list of moves made by the players
        
        Returns
        -------
        tuple[int, int]
            points for the players
        """
        if None in moves_made:
            return (0, 0)
        
        move1, move2 = moves_made
        if move1 == move2:
            return (0, 0)

        if move1 == self.move_mapping["rock"] and move2 == self.move_mapping["scissors"]:
            return (self.r, -self.r)
        if move1 == self.move_mapping["paper"] and move2 == self.move_mapping["rock"]:
            return (self.p, -self.p)
        if move1 == self.move_mapping["scissors"] and move2 == self.move_mapping["paper"]:
            return (self.s, -self.s)
        if move1 == self.move_mapping["scissors"] and move2 == self.move_mapping["rock"]:
            return (-self.r, self.r)
        if move1 == self.move_mapping["rock"] and move2 == self.move_mapping["paper"]:
            return (-self.p, self.p)
        if move1 == self.move_mapping["paper"] and move2 == self.move_mapping["scissors"]:
            return (-self.s, self.s)

    def play(self, rounds : int =1):
        """
        Play the game for a given number of rounds

        Parameters
        ----------
        rounds : int
            number of rounds to play

        Returns
        -------
        dict
            game information
        """
        total_moves_made = list()
        total_points = list()
        for _ in range(rounds):
            round_moves_made = self.play_round()
            
            round_points = self._calculate_points(round_moves_made)

            # update player context
            points1, points2 = round_points
            winner_idx = 0 if points1 > points2 else 1 if points2 > points1 else -1

            if winner_idx == -1:
                for player in self.players:
                    player.append_context({
                        "role": PlayerRole.ASSISTANT.value,
                        "content": self._content_wrapper(
                            f"[hint] The round ended in a tie. Both players made the same move: {round_moves_made[winner_idx]}.\nYou scored {round_points[0]} points.\n"
                        )
                    })

            else:
                self.players[winner_idx].append_context({
                    "role": PlayerRole.ASSISTANT.value,
                    "content": self._content_wrapper(
                        f"[hint] You won the round. You made the move: {round_moves_made[winner_idx]}. Your opponent made the move: {round_moves_made[1-winner_idx]}.\nYou scored {round_points[winner_idx]} points.\n"
                    )
                })
                self.players[1 - winner_idx].append_context({
                    "role": PlayerRole.ASSISTANT.value,
                    "content": self._content_wrapper(
                        f"[hint] You lost the round. You made the move: {round_moves_made[1-winner_idx]}. Your opponent made the move: {round_moves_made[winner_idx]}.\nYou scored {round_points[1-winner_idx]} points.\n"
                    )
                })

            total_moves_made.append(round_moves_made)
            total_points.append(round_points)

        # both players are inactive after the game ends
        for player in self.players:
            player.active = False

        # game info generation
        valid_outcomes = [None not in moves_made for moves_made in total_moves_made]
        
        info = dict()
        info["valid_outcomes"] = valid_outcomes
        for i, player in enumerate(self.players):
            info[f"player_{i}_context"] = player.context
            info[f"player_{i}_points"] = [points[i] for points in total_points]
            info[f"player_{i}_moves"] = [moves[i] for moves in total_moves_made]
        info["total_tokens"] = [statistics.mean(tokens) for tokens in self.total_tokens]
        info["game_settings"] = {
            "r": self.r,
            "p": self.p,
            "s": self.s,
            "move_mapping": self.move_mapping,
        }
        # single-round optimal strategy
        info["single_round_optimal_strategy"] = optimal_strategy(self.p, self.r, self.s)
        # multi-round player strategy
        for i, player in enumerate(self.players):
            player_strategy = Counter(info[f"player_{i}_moves"])
            player_strategy = {k: v / len(info[f"player_{i}_moves"]) for k, v in player_strategy.items()}
            info[f"player_{i}_strategy"] = player_strategy
        
        return info
