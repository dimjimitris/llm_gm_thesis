from chat.bedrock import (
    Player,
    BedrockChat,
)

from prompts.rps import (
    RPS_PROMPTS,
)

INITIAL_PROMPT = RPS_PROMPTS["initial"]

import random

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