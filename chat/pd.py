from chat.bedrock import BedrockChat
from chat.player import Player, BedrockPlayer
from utils.globals import PlayerRole
from utils.pd import optimal_strategy

from collections import Counter
import random
import re
import json
import tabulate
import statistics

class PrisonersDilemma(BedrockChat):
    def __init__(
        self,
        id: int,
        players: list[Player],
        game_settings_type: str,
        game_settings: dict,
        log_dir: str,
    ):
        super().__init__(
            id,
            players,
            "pd",
            game_settings_type,
            log_dir,
        )
        self.aa = game_settings["aa"]
        self.ab = game_settings["ab"]
        self.ba = game_settings["ba"]
        self.bb = game_settings["bb"]
        self.a = game_settings["a"]
        self.b = game_settings["b"]
        self.self_consistencies = [list() for _ in range(len(self.players))]

    def play_round(self, total_moves_made : list[list[str]]) -> tuple[list[str], list[int]]:

        curr_player_idx = 0
        token_counts = [0, 0]
        
        for idx, player in enumerate(self.players):
            other_idx = 1 - idx
            recommendation = "Please choose your move."

            if self.players[other_idx].active:
                player.append_context(
                    PlayerRole.USER,
                    "[hint] Let's play another round. " + recommendation + "\n",
                )
            else:
                if self.players[other_idx].fresh:
                    player.append_context(
                        PlayerRole.USER,
                        "[hint] Let's play this game. You are playing against a fresh player. " + recommendation + "\n",
                    )
                else:
                    player.append_context(
                        PlayerRole.USER,
                            "[hint] Let's play this game. You are playing against an experienced player. " + recommendation + "\n",
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

            resp_aux = list(enumerate(responses))
            random.shuffle(resp_aux)

            for idx, response in resp_aux:
                if self._parse_move(response) == max_move:
                    player.context = players[idx].context
                    self.self_consistencies[player.id].append({
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
            return False, f"You may structure your response however you like, but it should contain a move message. Move messages begin with the tag [move] not containing other tags, which is followed by your optional explanation in parentheses, and end with a valid move: '{self.a}' or '{self.b}'. Nested parentheses are not allowed.\nFormat: [move] (Optional explanation here) Your move here"

    def _is_move_message(self, msg : str) -> bool:
        """
        Check if the message is an move message

        Parameters
        ----------
        msg : str
            message to check

        Returns
        -------
        bool
            whether the message is an move message
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

        pattern = rf'\[move\](?: \(([^)]+)\))? ({re.escape(self.a)}|{re.escape(self.b)})'
        matches = re.findall(pattern, msg_aux)

        if len(matches) == 0:
            return False, f"You may structure your response however you like, but it should contain a move message. Move messages begin with the tag [move] not containing other tags, which is followed by your optional explanation in parentheses, and end with a valid move: '{self.a}' or '{self.b}'. Nested parentheses are not allowed.\nFormat: [move] (Optional explanation here) Your move here"

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

        valid, error_msg = self._validate_move(msg)
        if not valid:
            return None

        msg_aux = msg.lower().strip()

        pattern = rf'\[move\](?: \(([^)]+)\))? ({re.escape(self.a)}|{re.escape(self.b)})'
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
        if move1 == self.a and move2 == self.a:
            return (self.aa, self.aa)
        if move1 == self.b and move2 == self.b:
            return (self.bb, self.bb)
        if move1 == self.a and move2 == self.b:
            return (self.ab, self.ba)
        if move1 == self.b and move2 == self.a:
            return (self.ba, self.ab)
        
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
        move_mapping_str = json.dumps({ "a": self.a, "b": self.b }, indent=2)
        payoff_matrix_str = tabulate.tabulate(
            tabular_data=[
                [self.a, (self.aa, self.aa), (self.ab, self.ba)],
                [self.b, (self.ba, self.ab), (self.bb, self.bb)],
            ],
            headers=["", self.a, self.b],
            tablefmt="github",
        )

        # log model information
        for player in [p for p in self.players if isinstance(p, BedrockPlayer)]:
            player.save_log(f"Player: {player.unique_name}\n")
            player.save_log(f"Model: {player.model_id}\n")
            player.save_log(f"Temperature: {player.temp}\n")
            player.save_log(f"Max tokens: {player.max_tokens}\n")

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
                            f"[hint] The round ended. Both players choose the same move: {round_moves_made[winner_idx]}.\nYou scored {round_points[0]} points.\n",
                        )

                else:
                    self.players[winner_idx].append_context(
                        PlayerRole.USER,
                        f"[hint] The round ended. You choose the move: {round_moves_made[winner_idx]}. Your opponent choose the move: {round_moves_made[1-winner_idx]}.\nYou scored {round_points[winner_idx]} points.\n",
                    )
                    self.players[1 - winner_idx].append_context(
                        PlayerRole.USER,
                        f"[hint] The round ended. You choose the move: {round_moves_made[1-winner_idx]}. Your opponent choose the move: {round_moves_made[winner_idx]}.\nYou scored {round_points[1-winner_idx]} points.\n",
                    )
            else:
                for player in self.players:
                    player.append_context(
                        PlayerRole.USER,
                        f"[hint] The round ended abnormally. You scored 0 points.\n",
                    )

            total_moves_made.append(round_moves_made)
            total_points.append(round_points)

            # log player context
            for player in self.players:
                player.save_context()

            # game info generation
            info = self._generate_info(total_tokens, total_moves_made, total_points)

            # log the game information
            self.save_info(info)

        # both players are inactive after the game ends
        for player in self.players:
            player.active = False

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
 
        info["valid_outcomes"] = [None not in moves_made for moves_made in total_moves_made]
        for i, player in enumerate(self.players):
            info[f"player_{i}_context"] = player.context
            info[f"player_{i}_points"] = [points[i] for points in total_points]
            info[f"player_{i}_total_points"] = sum(points[i] for points in total_points)
            info[f"player_{i}_average_points"] = statistics.mean(points[i] for points in total_points)
            info[f"player_{i}_moves"] = [moves[i] for moves in total_moves_made]
            info[f"player_{i}_tokens"] = [tokens[i] for tokens in total_tokens]

            info[f"player_{i}_rates"] = {
                "win": statistics.mean(int(points > 0) for points in info[f"player_{i}_points"]),
                "loss": statistics.mean(int(points < 0) for points in info[f"player_{i}_points"]),
                "tie": statistics.mean(int(points == 0) for points in info[f"player_{i}_points"]),
            }

        info["game_settings"] = {
            "a": self.a,
            "b": self.b,
            "aa": self.aa,
            "ab": self.ab,
            "ba": self.ba,
            "bb": self.bb,
        }
        # single-round optimal strategy
        info["single_round_optimal_strategy"] = optimal_strategy(self.aa, self.ab, self.ba, self.bb)
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

        # add self-consistency information
        for i, player in enumerate(self.players):
            info[f"player_{i}_sc"] = self.self_consistencies[player.id]

        return info