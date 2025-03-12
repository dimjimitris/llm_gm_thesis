from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

from chat.player import Player

import os
import random
import boto3

class BedrockChat:
    """
    Interface to chatting with Bedrock AI models. There is user, and assistant role separation. A system prompt is initially provided to AI agents. We will be using models that support system prompts and the converse API.

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
    """
    def __init__(
        self,
        id: int,
        game_type: str,
        log_path: str,
        temp: float,
        max_tokens: int,
        model_id: str,
    ):
        """
        Parameters
        ----------
        id : int
            game id
        game_type : str
            type of the game, e.g., "rps"
        log_path : str
            path to the root log directory
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        model_id : str
            bedrock model id
        """
        self.id = id
        self.game_type = game_type
        self.unique_name = f"{self.game_type}_{self.id}"

        log_path_aux = os.path.join(log_path, game_type, self.unique_name)
        os.makedirs(log_path_aux, exist_ok=True)
        self.game_log = os.path.join(log_path_aux, "game.log")
        self.info_log = os.path.join(log_path_aux, "game.info")

        self.temp = temp
        self.max_tokens = max_tokens
        self.model_id = model_id

        self.players : list[Player] = list()

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

        return {
            "output_text": output_text,
            "input_tokens": int(usage["inputTokens"]),
            "output_tokens": int(usage["outputTokens"]),
            "total_tokens": int(usage["totalTokens"]),
        }