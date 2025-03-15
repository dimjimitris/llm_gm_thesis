from typing import Iterable
from chat.bedrock import BedrockChat
from chat.player import Player
from utils.globals import PlayerRole
from utils.rps import optimal_strategy

import random
import statistics
import tabulate
import json
from collections import Counter

class RockPaperScissorsGame(BedrockChat):
    """
    Represents a Rock-Paper-Scissors game. Allows for easy creation of counterfactual rps games.

    Attributes
    ----------
    id : int
        game id
    players : list
        list of player objects, should have two players
    game_type : str
        type of the game, e.g., "rps"
    unique_name : str
        unique name for the game, should be {game_type}_{id}
    game_file : str
        path to the game's log file
    info_file : str
        path to the game's info file
    temp : float
        temperature parameter for sampling
    max_tokens : int
        maximum number of tokens to generate
    model_id : str
        bedrock model id
    r : str
        reward for rock beating scissors
    p : str
        reward for paper beating rock
    s : str
        reward for scissors beating paper
    move_mapping : dict
        mapping of moves to moves
    system_prompt : str
        system prompt for the game
    rand_player_seq : bool
        whether to randomize the player sequence or not on each round. If False, player_0 will always play first.
    players : list
        list of player objects, should have two players
    """
    def __init__(
        self,
        id: int,
        players: list[Player],
        game_settings_type: str,
        game_settings: dict,
        model_id: str,
        log_dir: str,
        temp: float,
        max_tokens: int,
        rand_player_seq : bool = True,
    ):
        """
        Parameters
        ----------
        id : int
            game id
        players : list
            list of player objects, should have two players
        game_settings_type : str
            game settings type, one of ["eq1", "eq2", "r2", "p2", "s2"]
        game_settings : dict
            dictionary containing the game settings
        model_id : str
            bedrock model id
        log_dir : str
            path to the root log directory
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        rand_player_seq : bool
            whether to randomize the player sequence or not on each round. If False, player_0 will always play first.
        """
        super().__init__(
            id,
            players,
            "rps",
            game_settings_type,
            model_id,
            log_dir,
            temp,
            max_tokens,
        )
        self.r = game_settings["r"]
        self.p = game_settings["p"]
        self.s = game_settings["s"]
        self.move_mapping : dict = game_settings["move_mapping"]
        self.system_prompt = players[0].system_prompt
        self.rand_player_seq = rand_player_seq
        self.players = players

    def play_round(self) -> tuple[list[str], list[int]]:
        """
        Play a round of the game

        Returns
        -------
        tuple[list[str], list[int]]
            moves made by the players and the token counts for the players
        """
        curr_player_idx = random.choice([0, int(self.rand_player_seq)])
        token_counts = [0, 0]

        for idx, player in enumerate(self.players):
            other_idx = 1 - idx
            recommendation = "Please make your move." if idx == curr_player_idx else "The other player made their move. Please make a move too."

            if self.players[other_idx].active:
                player.append_context({
                    "role": PlayerRole.USER.value,
                    "content": self._content_wrapper(
                        "[hint] Let's play another round. " + recommendation + "\n"
                    )
                })
            else:
                if self.players[other_idx].fresh:
                    player.append_context({
                        "role": PlayerRole.USER.value,
                        "content": self._content_wrapper(
                            "[hint] Let's play rock-paper-scissors. You are playing against a fresh player. " + recommendation + "\n"
                        )
                    })
                else:
                    player.append_context({
                        "role": PlayerRole.USER.value,
                        "content": self._content_wrapper(
                            "[hint] Let's play rock-paper-scissors. You are playing against an experienced player. " + recommendation + "\n"
                        )
                    })

        moves_made = [None, None]
        for idx, player in [
            (curr_player_idx, self.players[curr_player_idx]),
            (1 - curr_player_idx, self.players[1 - curr_player_idx])
            ]:
            other_idx = 1 - idx
            other_player = self.players[other_idx]

            response_text, tokens = self._player_response(player)
            token_counts[idx] += tokens

            # log the response
            self.save_log(f"[player_{idx}] {response_text}\n")

            if "[abort]" in response_text:
                player.append_context({
                    "role": PlayerRole.ASSISTANT.value,
                    "content": self._content_wrapper(
                        response_text
                    )
                })
                other_player.append_context({
                    "role": PlayerRole.USER.value,
                    "content": self._content_wrapper(
                        "[hint] The other player has aborted the game. The game has ended.\n"
                    )
                })
                break

            if response_text.startswith("[move]"):
                moves_made[idx] = self._parse_move(response_text)
                player.append_context({
                    "role": PlayerRole.ASSISTANT.value,
                    "content": self._content_wrapper(
                        response_text
                    )
                })
                player.append_context({
                    "role": PlayerRole.USER.value,
                    "content": self._content_wrapper(
                        "[hint] Move made. Waiting for the game to end.\n"
                    )
                })
        
        for player in self.players:
            player.active = True
        
        return moves_made, token_counts

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

            # log the response
            player.save_log(f"[assistant] {response_text}\n")

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
                    f"[hint] An error occurred. Please resend the previous message with the following correction, without indicating in any way that you have made a correction to a prior message: \n \"{error_msg}\"\n"
                )
            })

            # log the error
            player.save_log(f"[error] {error_msg}\n")

            error_cnt += 1
            if error_cnt >= 5:
                response_text = "[abort]\n"
                break
            
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
        
        return False, "Your output should be a move message. Move messages begin with the tag [move], which is followed by your optional explanation in parentheses, and end with a valid move: 'rock', 'paper', or 'scissors'.\nFormat: [move] (Optional explanation here) Your move here"
    
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
            return False, "Your move must begin with the tag [move], which is followed by your optional explanation in parentheses, and end with a valid move: 'rock', 'paper', or 'scissors'.\nFormat: [move] (Optional explanation here) Your move here"
        
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

    def play(self, rounds : int) -> dict:
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
        # log game start
        move_mapping_str = json.dumps(self.move_mapping, indent=2)
        payoff_matrix_str = tabulate.tabulate(
            tabular_data=[
                [self.move_mapping["rock"], (0, 0), (-self.p, self.p), (self.r, -self.r)],
                [self.move_mapping["paper"], (self.p, -self.p), (0, 0), (-self.s, self.s)],
                [self.move_mapping["scissors"], (-self.r, self.r), (self.s, -self.s), (0, 0)]
            ],
            headers=["", self.move_mapping["rock"], self.move_mapping["paper"], self.move_mapping["scissors"]],
            tablefmt="github",
        )

        self.save_log(move_mapping_str + "\n" + payoff_matrix_str + "\n")
        self.save_log(f"{rounds} rounds.\n")
        for player in self.players:
            player.save_log(move_mapping_str + "\n" + payoff_matrix_str + "\n")
            player.save_log(f"{rounds} rounds.\n")
        

        total_tokens = list()
        total_moves_made = list()
        total_points = list()
        for r in range(rounds):
            round_moves_made, token_counts = self.play_round()
            total_tokens.append(token_counts)
            round_points = self._calculate_points(round_moves_made)

            # update player context
            points1, points2 = round_points
            winner_idx = 0 if points1 > points2 else 1 if points2 > points1 else -1

            # log the round results
            self.save_log(f"Round {r} results: {round_moves_made}, {round_points}\n")

            if None not in round_moves_made:
                if winner_idx == -1:
                    for player in self.players:
                        player.append_context({
                            "role": PlayerRole.USER.value,
                            "content": self._content_wrapper(
                                f"[hint] The round ended in a tie. Both players made the same move: {round_moves_made[winner_idx]}.\nYou scored {round_points[0]} points.\n"
                            )
                        })

                else:
                    self.players[winner_idx].append_context({
                        "role": PlayerRole.USER.value,
                        "content": self._content_wrapper(
                            f"[hint] You won the round. You made the move: {round_moves_made[winner_idx]}. Your opponent made the move: {round_moves_made[1-winner_idx]}.\nYou scored {round_points[winner_idx]} points.\n"
                        )
                    })
                    self.players[1 - winner_idx].append_context({
                        "role": PlayerRole.USER.value,
                        "content": self._content_wrapper(
                            f"[hint] You lost the round. You made the move: {round_moves_made[1-winner_idx]}. Your opponent made the move: {round_moves_made[winner_idx]}.\nYou scored {round_points[1-winner_idx]} points.\n"
                        )
                    })
            else:
                for player in self.players:
                    player.append_context({
                        "role": PlayerRole.USER.value,
                        "content": self._content_wrapper(
                            f"[hint] The round ended abnormally. You scored 0 points.\n"
                        )
                    })

            total_moves_made.append(round_moves_made)
            total_points.append(round_points)

        # both players are inactive after the game ends
        for player in self.players:
            player.active = False

        # log player context
        for player in self.players:
            player.save_context()

        # game info generation
        info = self._generate_info(total_tokens, total_moves_made, total_points)

        # log the game information
        self.save_info(info)

        return info
    
    def _generate_info(
        self,
        total_tokens : list[list[int]],
        total_moves_made : list[list[str]],
        total_points : list[list[int]],
    ) -> dict:
        """
        Generate the game information

        Parameters
        ----------
        total_tokens : list[list[int]]
            list of token counts for each round
        total_moves_made : list[list[str]]
            list of moves made by the players for each round
        total_points : list[list[int]]
            list of points scored by the players for each round

        Returns
        -------
        dict
            game information
        """
        valid_outcomes = [None not in moves_made for moves_made in total_moves_made]
        
        info = dict()
        info["valid_outcomes"] = valid_outcomes
        for i, player in enumerate(self.players):
            info[f"player_{i}_context"] = player.context
            info[f"player_{i}_points"] = [points[i] for points in total_points]
            info[f"player_{i}_moves"] = [moves[i] for moves in total_moves_made]
            

            info[f"player{i}_rates"] = {
                "win": self._mean_aux(1 for points in info[f"player_{i}_points"] if points > 0),
                "loss": self._mean_aux(1 for points in info[f"player_{i}_points"] if points < 0),
                "tie": self._mean_aux(1 for points in info[f"player_{i}_points"] if points == 0),
            }

        info["total_tokens"] = [self._mean_aux(tokens) for tokens in total_tokens]
        info["game_settings"] = {
            "r": self.r,
            "p": self.p,
            "s": self.s,
            "move_mapping": self.move_mapping,
        }
        # single-round optimal strategy
        info["single_round_optimal_strategy"] = optimal_strategy(self.r, self.p, self.s)
        # multi-round player strategy
        for i, player in enumerate(self.players):
            player_strategy = Counter(info[f"player_{i}_moves"])
            player_strategy = {k: v / len(info[f"player_{i}_moves"]) for k, v in player_strategy.items()}
            info[f"player_{i}_strategy"] = player_strategy

        # add log paths to info
        info["game_log"] = self.game_file
        for i, player in enumerate(self.players):
            info[f"player_{i}_log"] = player.player_file

        return info
    
    def _mean_aux(self, data : Iterable[int]) -> float:
        """
        Calculate the mean of the data

        Parameters
        ----------
        data : Iterable[int]
            data to calculate the mean of

        Returns
        -------
        float
            mean of the data
        """
        try:
            return statistics.mean(data)
        except statistics.StatisticsError:
            return 0.0