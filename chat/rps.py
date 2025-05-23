from chat.bedrock import BedrockChat
from chat.player import Player, BedrockPlayer
from utils.globals import PlayerRole
from utils.rps import optimal_strategy

import random
import statistics
import tabulate
import json
from collections import Counter
import re
import copy

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
    r : str
        reward for rock beating scissors
    p : str
        reward for paper beating rock
    s : str
        reward for scissors beating paper
    move_mapping : dict
        mapping of moves to moves
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
        log_dir: str,
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
        log_dir : str
            path to the root log directory
        rand_player_seq : bool
            whether to randomize the player sequence or not on each round. If False, player_0 will always play first.
        trees_of_thought : list
            lists of thoughts of players
        """
        super().__init__(
            id,
            players,
            "rps",
            game_settings_type,
            log_dir,
        )
        self.r = game_settings["r"]
        self.p = game_settings["p"]
        self.s = game_settings["s"]
        self.move_mapping : dict = game_settings["move_mapping"]
        self.rand_player_seq = rand_player_seq
        self.trees_of_thought = [list() for _ in range(len(players))]

    def play_round(self, total_moves_made : list[list[str]]) -> tuple[list[str], list[int]]:
        """
        Play a round of the game

        Parameters
        ----------
        total_moves_made : list[list[str]]
            list of moves made by the players for each round so far

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
                player.append_context(
                    PlayerRole.USER,
                    "[hint] Let's play another round. " + recommendation + "\n",
                )
            else:
                if self.players[other_idx].fresh:
                    player.append_context(
                        PlayerRole.USER,
                        "[hint] Let's play rock-paper-scissors. You are playing against a fresh player. " + recommendation + "\n",
                    )
                else:
                    player.append_context(
                        PlayerRole.USER,
                            "[hint] Let's play rock-paper-scissors. You are playing against an experienced player. " + recommendation + "\n",
                    )

        moves_made = [None, None]
        for idx, player in [
            (curr_player_idx, self.players[curr_player_idx]),
            (1 - curr_player_idx, self.players[1 - curr_player_idx])
            ]:
            other_idx = 1 - idx
            other_player = self.players[other_idx]

            response_text, tokens = self._player_response(player, total_moves_made)
            token_counts[idx] += tokens

            # log the response
            self.save_log(f"[player_{idx}] {response_text}\n")

            if "[abort]" in response_text:
                player.append_context(
                    PlayerRole.ASSISTANT,
                    response_text,
                )
                other_player.append_context(
                    PlayerRole.USER,
                    "[hint] The other player has aborted the game. The game has ended.\n",
                )
                break

            # if we get to this point, _player_response() has returned a valid response
            # that response has already passed the _is_move_message() check
            # so we can safely parse the move
            moves_made[idx] = self._parse_move(response_text)
            player.append_context(
                PlayerRole.ASSISTANT,
                response_text,
            )
            player.append_context(
                PlayerRole.USER,
                "[hint] Move made. Waiting for the game to end.\n",
            )
        
        for player in self.players:
            player.active = True
        
        return moves_made, token_counts

    def _player_response(
        self,
        player : Player,
        total_moves_made : list[list[str]],
    ):
        if (player.k < 2):
            return self._player_response_aux(player, total_moves_made)
        else:
            total_tokens = 0
            responses = list()
            players : list[Player] = list()
            for i in range(player.k):
                new_player : BedrockPlayer = player.copy(i)
                response, tokens = self._player_response_aux(new_player, total_moves_made)
                total_tokens += tokens
                responses.append(response)
                players.append(new_player)
            
            # voting phase - most popular move wins, pick randomly a response with that move
            move_counts = Counter(self._parse_move(response) for response in responses)
            max_count = max(move_counts.values())
            max_moves = [move for move, count in move_counts.items() if count == max_count]
            max_move = random.choice(max_moves)
            for idx, response in enumerate(responses):
                if self._parse_move(response) == max_move:
                    player.context = players[idx].context
                    self.trees_of_thought[player.id].append({
                        "options": responses,
                        "opt_id": idx,
                    })
                    return response, total_tokens

    def _player_response_aux(
        self,
        player : Player,
        total_moves_made : list[list[str]],
    ) -> tuple[str, int]:
        tokens = 0
        response_text = None
        error_cnt = 0
        while True:
            response_obj = player.generate_response(total_moves_made)
            response_text : str = response_obj["output_text"]
            if not response_text.endswith("\n"):
                response_text += "\n"

            tokens += response_obj["total_tokens"]

            # log the response
            player.save_log(f"[assistant] {response_text}\n")

            is_valid, error_msg = self._validate_response(response_text)
            if is_valid:
                break

            player.append_context(
                PlayerRole.ASSISTANT,
                response_text,
            )
            player.append_context(
                PlayerRole.USER,
                f"[hint] An error occurred. Please resend the previous message with the following correction, without indicating in any way that you have made a correction to a prior message: \n \"{error_msg}\"\n",
            )

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
        if self._is_move_message(msg):
            return self._validate_move(msg)
        else:
            return False, "You may structure your response however you like, but it should contain a move message. Move messages begin with the tag [move] and not contain other tags, which is followed by your optional explanation in parentheses, and end with a valid move: 'rock', 'paper', or 'scissors'.\nFormat: [move] (Optional explanation here) Your move here"
    
    def _is_move_message(self, msg : str) -> bool:
        """
        Check if the message is a move message

        Parameters
        ----------
        msg : str
            message to check

        Returns
        -------
        bool
            whether the message is a move message
        """
        pattern = r"\[[^\]]+\]"
        matches = re.findall(pattern, msg)
        return len(matches) == 1 and matches[0] == "[move]"

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
        pattern = r'\[move\](?: \(([^)]+)\))? (rock|paper|scissors)'
        matches = re.findall(pattern, msg_aux)

        if len(matches) == 0:
            return False, "You may structure your response however you like, but it should contain a move message. Move messages begin with the tag [move] and not contain other tags, which is followed by your optional explanation in parentheses, and end with a valid move: 'rock', 'paper', or 'scissors'.\nFormat: [move] (Optional explanation here) Your move here"

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
        msg_aux = msg.lower().strip()
        pattern = r'\[move\](?: \(([^)]+)\))? (rock|paper|scissors)'
        matches = re.findall(pattern, msg_aux)
       
        return matches[0][-1]
    
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

        # log model information
        for player in [p for p in self.players if isinstance(p, BedrockPlayer)]:
            player.save_log(f"Player: {player.unique_name}\n")
            player.save_log(f"Model: {player.model_id}\n")
            player.save_log(f"Temperature: {player.temp}\n")
            player.save_log(f"Max tokens: {player.max_tokens}\n")
            player.save_log(f"Random player sequence: {self.rand_player_seq}\n")

        self.save_log(move_mapping_str + "\n" + payoff_matrix_str + "\n")
        self.save_log(f"{rounds} rounds.\n")
        for player in self.players:
            player.save_log(move_mapping_str + "\n" + payoff_matrix_str + "\n")
            player.save_log(f"{rounds} rounds.\n")
        

        total_tokens = list()
        total_moves_made = list()
        total_points = list()
        for r in range(rounds):
            round_moves_made, token_counts = self.play_round(total_moves_made)
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
                        player.append_context(
                            PlayerRole.USER,
                            f"[hint] The round ended in a tie. Both players made the same move: {round_moves_made[winner_idx]}.\nYou scored {round_points[0]} points.\n",
                        )

                else:
                    self.players[winner_idx].append_context(
                        PlayerRole.USER,
                        f"[hint] You won the round. You made the move: {round_moves_made[winner_idx]}. Your opponent made the move: {round_moves_made[1-winner_idx]}.\nYou scored {round_points[winner_idx]} points.\n",
                    )
                    self.players[1 - winner_idx].append_context(
                        PlayerRole.USER,
                        f"[hint] You lost the round. You made the move: {round_moves_made[1-winner_idx]}. Your opponent made the move: {round_moves_made[winner_idx]}.\nYou scored {round_points[1-winner_idx]} points.\n",
                    )
            else:
                for player in self.players:
                    player.append_context(
                        PlayerRole.USER,
                        f"[hint] The round ended abnormally. You scored 0 points.\n",
                    )

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
        info = dict()
        for player in self.players:
            info[f"player_{player.id}_player_type"] = player.player_type

        # add model information to info
        for player in [p for p in self.players if isinstance(p, BedrockPlayer)]:
            info[f"player_{player.id}_model_id"] = player.model_id
            info[f"player_{player.id}_temperature"] = player.temp
            info[f"player_{player.id}_max_tokens"] = player.max_tokens
        info["random_player_sequence"] = self.rand_player_seq

 
        info["valid_outcomes"] = [None not in moves_made for moves_made in total_moves_made]
        for i, player in enumerate(self.players):
            info[f"player_{i}_context"] = player.context
            info[f"player_{i}_points"] = [points[i] for points in total_points]
            info[f"player_{i}_average_points"] = statistics.mean(points[i] for points in total_points)
            info[f"player_{i}_moves"] = [moves[i] for moves in total_moves_made]
            info[f"player_{i}_tokens"] = [tokens[i] for tokens in total_tokens]

            info[f"player_{i}_rates"] = {
                "win": statistics.mean(int(points > 0) for points in info[f"player_{i}_points"]),
                "loss": statistics.mean(int(points < 0) for points in info[f"player_{i}_points"]),
                "tie": statistics.mean(int(points == 0) for points in info[f"player_{i}_points"]),
            }

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

        # add player system prompts
        for i, player in enumerate(self.players):
            info[f"player_{i}_prompt"] = player.system_prompt

        # add trees of thought
        for i, player in enumerate(self.players):
            info[f"player_{i}_tot"] = self.trees_of_thought[player.id]

        return info