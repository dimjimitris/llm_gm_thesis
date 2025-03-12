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

INITIAL_PROMPT = RPS_PROMPTS["initial"]

import random
import tabulate
import json

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
            response_text = self._player_response(curr_player)

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
    ):
        response_text = None
        error_cnt = 0
        while True:
            response_obj = self._generate_response(player)
            response_text : str = response_obj["output_text"]
            if not response_text.endswith("\n"):
                response_text += "\n"

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
                return "[abort]\n"
            
        return response_text

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