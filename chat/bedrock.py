from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

from chat.player import Player

import os
import boto3
import json

class BedrockChat:
    """
    Interface to chatting with Bedrock AI models. There is user, and assistant role separation. A system prompt is initially provided to AI agents. We will be using models that support system prompts and the converse API.

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
    """
    def __init__(
        self,
        id: int,
        players: list[Player],
        game_type: str,
        game_settings_type: str,
        model_id: str,
        log_dir: str,
        temp: float,
        max_tokens: int,
    ):
        """
        Parameters
        ----------
        id : int
            game id
        players : list
            list of player objects, should have two players
        game_type : str
            type of the game, e.g., "rps"
        game_settings_type : str
            game settings type, one of ["eq1", "eq2", "r2", "p2", "s2"]
        model_id : str
            bedrock model id
        log_dir : str
            path to the root log directory
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        """
        self.id = id
        self.players = players
        self.game_type = game_type
        self.unique_name = f"{self.game_type}_{self.id}"

        log_path_aux = os.path.join(
            log_dir,
            game_type,
            game_settings_type,
            self.unique_name,
        )
        os.makedirs(log_path_aux, exist_ok=True)
        self.game_file = os.path.join(log_path_aux, "game.log")
        self.info_file = os.path.join(log_path_aux, "game.json")

        self.temp = temp
        self.max_tokens = max_tokens
        self.model_id = model_id

    def _system_prompt_wrapper(self, system_prompt: str):
        return [{ "text" : system_prompt }]
    
    def _content_wrapper(self, content: str):
        return [{ "text" : content }]

    def _generate_response(
        self,
        player : Player,
    ):
        # create a boto3 client for the LLM API
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name="us-west-2",
        )
        
        inference_config = {
            "maxTokens": self.max_tokens,
            "temperature": self.temp,
        }

        response = client.converse(
            modelId=self.model_id,
            messages=player.context,
            system=self._system_prompt_wrapper(player.system_prompt),
            inferenceConfig=inference_config,
        )

        output_text = response["output"]["message"]["content"][0]["text"]
        usage = response["usage"]

        print(f"{player.player_file}: {output_text}\n")

        return {
            "output_text": output_text,
            "input_tokens": int(usage["inputTokens"]),
            "output_tokens": int(usage["outputTokens"]),
            "total_tokens": int(usage["totalTokens"]),
        }
    
    def save_info(self, info) -> None:
        """
        Save game information to the info log file.

        Parameters
        ----------
        info : dict
            game information to save
        """
        with open(self.info_file, "w") as f:
            json.dump(info, f, indent=2)

    def load_info(self) -> dict:
        """
        Load game information from the info log file.

        Returns
        -------
        dict
            game information
        """
        with open(self.info_file, "r") as f:
            info = json.load(f)

        return info

    def _generate_info(self) -> dict:
        """
        Generate game information.
        """
        pass

    def save_log(self, log : str) -> None:
        """
        Append the log to the game's log file.

        Parameters
        ----------
        log : str
            log to append
        """
        with open(self.game_file, "a") as f:
            f.write(log)