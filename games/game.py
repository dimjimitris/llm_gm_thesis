from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

import os
import random
import boto3

class Game:
    """
    a generic game class that contains the basic structure of a game, inherited by all other game classes
    
    Methods
    -------
    play_game()
        plays the game
    calculate_final_points()
        calculates the final points of the game
    play()
        plays the game, calcuates the final points and returns the results properly formatted
    """
    def __init__(
        self,
        id : int,           # numeric identifier for the game, usually a timestamp
        game_type : str,    # the type of game being played
        prompt_path : str,  # the path to the initial prompt for the game
        log_path : str,     # the path to the general log directory
        model_id : str,     # the id of the LLM model to communicate with
        player_count : int, # the number of players in the game
        errors : dict,      # a dictionary of error messages to display to the user in erroneous situations
        MAX_ERRORS=5,       # the maximum number of errors allowed in the game until it is terminated
        MAX_MESSAGES=20,    # the maximum number of messages allowed in the game until it is terminated
        MAX_TOKENS=1_000,   # the maximum number of tokens allowed in agent outputs/responses
    ):
        self.id = id
        self.game_type = game_type
        self.unique_name = f"{self.game_type}_{self.id}"
        self.prompt_path = prompt_path

        self.model_id = model_id

        self.player_count = player_count
        self.first_player = random.randint(0, player_count - 1)
        self.contexts = [list() for _ in range(player_count)]
        self.system_prompts = list()

        # we create the unique log directory for logs of this game:
        # logs for the game and for each player are stored in files in this directory
        self.log_path = os.path.join(log_path, self.unique_name)
        # if the log path doesn't exist, create it
        os.makedirs(self.log_path, exist_ok=True)

        self.log_game = os.path.join(self.log_path, "game.log")
        self.log_agents = [
            os.path.join(self.log_path, f"agent_{i}.log") for i in range(self.player_count)
        ]

        self.errors = errors
        self.MAX_ERRORS = MAX_ERRORS
        self.MAX_MESSAGES = MAX_MESSAGES
        self.MAX_TOKENS = MAX_TOKENS

        self.messages = list()
        self.game_over = False
        self.move_made = False
        self.final_points = [None for _ in range(player_count)]
        self.final_points_logged = False
        self.total_tokens = [-1 for _ in range(player_count)]

    def _system_prompt_wrapper(self, system_prompt : str):
        return [{ "text" : system_prompt}]

    def _content_wrapper(self, content : str):
        return [{ "text" : content }]
    
    def _log(self, log_path : str, text : str, mode : str = "a", trail : str = ""):
        with open(log_path, mode) as f:
            f.write(text + trail)

    def _generate_response(
        self,
        messages : list[dict],
        log_agent_path : str,
        system_prompt : str,
    ):
        # create a boto3 client for the LLM API
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name="us-west-2",
        )

        # set up inference configuration
        inference_config = {
            "maxTokens" : self.MAX_TOKENS,
        }

        response = client.converse(
            modelId=self.model_id,
            messages=messages,
            system=self._system_prompt_wrapper(system_prompt),
            inferenceConfig=inference_config,
        )

        output_text = response["output"]["message"]["content"][0]["text"]

        print(f"{log_agent_path}: {output_text}")

        # format usage information to get input and output token counts
        usage_aux = response["usage"]
        input_tokens = int(usage_aux["inputTokens"])
        output_tokens = int(usage_aux["outputTokens"])
        total_tokens = int(usage_aux["totalTokens"])

        self._log(log_agent_path, output_text, mode="a", trail="\n")

        return {
            "output_text" : output_text,
            "input_tokens" : input_tokens,
            "output_tokens" : output_tokens,
            "total_tokens" : total_tokens,
        }
    
    def _format_game_outcome(
        self,
        player_cnt : int,
        player_points : int,
        player_logs,
        is_valid_outcome : bool,
        message_count : int,
        total_tokens : list[int],
    ):
        ret_val = dict()

        for i in range(player_cnt):
            ret_val[f"player_{i}_points"] = player_points[i]
            ret_val[f"player_{i}_log"] = player_logs[i]
        
        ret_val["is_valid_outcome"] = is_valid_outcome
        ret_val["message_count"] = message_count
        
        for i in range(player_cnt):
            ret_val[f"total_tokens_{i}"] = total_tokens[i]

        return ret_val

    def play_game(self) -> None:
        pass

    def calculate_final_points(self) -> None:
        pass

    def play(self) -> dict[str, any]:
        pass
