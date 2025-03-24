from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PlayerRole,
)

from utils.rps import (
    optimal_strategy as rps_optimal_strategy,
)

import os
import json
import boto3
import random
import copy

class Player:
    """
    Represents a player in the chat game.

    Attributes
    ----------
    id : int
        player id, should be 0 or 1
    unique_name : str
        unique name for the player, should be player_{id}
    system_prompt : str
        initial system prompt to start the game
    context : list
        list of chat history
    log_dir : str
        path to the log directory of the specific game played
    player_file : str
        path to the player's log file
    context_file : str
        path to the player's context file
    fresh : bool
        whether the player is fresh (True) or not (False) (non-fresh players are experienced players and created with the duplicate() method)
    active : bool
        an active player has already played some rounds against its current opponent
        an inactive player will now play their first round against their current opponent
    k : int
        number of responses to generate for ToT evaluation
    """
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
        k : int = 1,
    ):
        """
        Parameters
        ----------
        id : int
            player id, should be 0 or 1
        system_prompt : str
            initial system prompt to start the game
        log_dir : str
            path to the log directory of the specific game played
        k : int
            number of responses to generate for ToT evaluation
        """
        self.id = id
        self.unique_name = f"player_{self.id}"
        self.system_prompt = system_prompt
        self.context = list()
        self.log_dir = log_dir

        os.makedirs(log_dir, exist_ok=True)
        self.player_file = os.path.join(log_dir, f"{self.unique_name}.log")
        self.context_file = os.path.join(log_dir, f"{self.unique_name}.json")

        self.fresh = True
        self.active = False
        self.k = k

    def load_context(self) -> None:
        """
        loads the player's context from the context log file
        """
        with open(self.context_file, "r") as f:
            full_json = json.load(f)
            if len(full_json) == 0:
                self.context = list()
            else:
                self.context = full_json[-1]["context"]

    def save_context(self) -> None:
        """
        saves the player's context to the context log file
        """
        with open(self.context_file, "a+") as f:
            # if context file is not empty, it contains a list of dictionaries
            # so we need to put the current context entries in this list
            f.seek(0)
            full_json : list = json.load(f) if os.path.getsize(self.context_file) > 0 else []
            full_json.append({
                "system_prompt": self.system_prompt,
                "context": self.context,
            })
            f.seek(0)
            json.dump(full_json, f, indent=2)

    def append_context(self, role : PlayerRole, content : str) -> None:
        """
        appends the context to the player's context

        Parameters
        ----------
        role : str
            role of the entry, should be a value from PlayerRole
        content : str
            content of the entry
        """
        entry = {
            "role": role.value,
            "content": Player._content_wrapper(content)
        }

        if len(self.context) == 0:
            self.context.append(entry)
            return
        
        last_entry = self.context[-1]
        if last_entry["role"] == entry["role"]:
            last_entry_text = Player._content_unwrapper(last_entry["content"])
            entry_text = Player._content_unwrapper(entry["content"])
            # if the entry_text has a tag, remove it
            if entry_text.startswith("[hint] ") or entry_text.startswith("[move] "):
                entry_text = entry_text[7:]
            elif entry_text.startswith("[hint]") or entry_text.startswith("[move]"):
                entry_text = entry_text[6:]
            last_entry["content"] = Player._content_wrapper(f"{last_entry_text}\n{entry_text}")
        else:
            self.context.append(entry)

    def save_log(self, log: str) -> None:
        """
        Append the log to the player's log file.

        Parameters
        ----------
        log : str
            log to append
        """
        with open(self.player_file, "a") as f:
            f.write(log)
    
    def generate_response(
        self,
        total_moves_made: list[list[str]],
    ):
        """
        Generate a response from the player's model.

        Parameters
        ----------
        total_moves_made : list
            list of all moves made by both players in previous rounds

        Returns
        -------
        dict
            a dictionary containing the output text, input tokens, output tokens, and total tokens
        """
        pass
    
    @staticmethod
    def _system_prompt_wrapper(system_prompt: str):
        return [{ "text" : system_prompt }]

    @staticmethod
    def _content_wrapper(content: str):
        return [{ "text" : content }]

    @staticmethod
    def _content_unwrapper(content: str):
        return content[0]["text"]
    
    def copy(self, idx : int) -> "Player":
        pass
    
class BedrockPlayer(Player):
    """
    Represents an AI player in the chat game.

    Attributes
    ----------
    id : int
        player id, should be 0 or 1
    unique_name : str
        unique name for the player, should be player_{id}
    system_prompt : str
        initial system prompt to start the game
    context : list
        list of chat history
    player_file : str
        path to the player's log file
    context_file : str
        path to the player's context file
    fresh : bool
        whether the player is fresh (True) or not (False) (non-fresh players are experienced players and created with the duplicate() method)
    active : bool
        an active player has already played some rounds against its current opponent
        an inactive player will now play their first round against their current opponent
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
        system_prompt: str,
        log_dir: str,
        k : int,
        model_id: str,
        temp: float,
        max_tokens: int,
    ):
        """
        Parameters
        ----------
        id : int
            player id, should be 0 or 1
        system_prompt : str
            initial system prompt to start the game
        log_dir : str
            path to the log directory of the specific game played
        k : int
            number of responses to generate for ToT evaluation
        model_id : str
            bedrock model id
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        """
        super().__init__(id, system_prompt, log_dir, k)

        self.temp = temp
        self.max_tokens = max_tokens
        self.model_id = model_id

    def generate_response(
        self,
        total_moves_made: list[list[str]],
    ):
        """
        Generate a response from the player's model.

        Returns
        -------
        dict
            a dictionary containing the output text, input tokens, output tokens, and total tokens
        """
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
            messages=self.context,
            system=BedrockPlayer._system_prompt_wrapper(self.system_prompt),
            inferenceConfig=inference_config,
        )

        output_text = response["output"]["message"]["content"][0]["text"]
        usage = response["usage"]

        print(f"{self.player_file}: {output_text}\n")

        return {
            "output_text": output_text,
            "input_tokens": int(usage["inputTokens"]),
            "output_tokens": int(usage["outputTokens"]),
            "total_tokens": int(usage["totalTokens"]),
        }
    
    def copy(self, idx : int) -> "BedrockPlayer":
        new_player = BedrockPlayer(
            10*(idx + 1) + self.id,
            self.system_prompt,
            self.log_dir,
            1,
            self.model_id,
            self.temp,
            self.max_tokens,
        )
        new_player.active = self.active
        new_player.fresh = self.fresh
        new_player.context = copy.deepcopy(self.context)
        return new_player
    
class SingleRoundEquilibriumPlayer(Player):
    """
    Represents a single-round equilibrium player in the chat game.

    Attributes
    ----------
    id : int
        player id, should be 0 or 1
    unique_name : str
        unique name for the player, should be player_{id}
    system_prompt : str
        initial system prompt to start the game
    context : list
        list of chat history
    player_file : str
        path to the player's log file
    context_file : str
        path to the player's context file
    fresh : bool
        whether the player is fresh (True) or not (False) (non-fresh players are experienced players and created with the duplicate() method)
    active : bool
        an active player has already played some rounds against its current opponent
        an inactive player will now play their first round against their current opponent
    r : float
        reward for rock
    p : float
        reward for paper
    s : float
        reward for scissors
    move_mapping : dict
        mapping of moves to moves in the game
    """
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
        game_settings: dict,
    ):
        """
        Parameters
        ----------
        id : int
            player id, should be 0 or 1
        system_prompt : str
            initial system prompt to start the game
        log_dir : str
            path to the log directory of the specific game played
        game_settings : dict
            game settings for the rock-paper-scissors game
        """
        super().__init__(id, system_prompt, log_dir)
        self.r = game_settings["r"]
        self.p = game_settings["p"]
        self.s = game_settings["s"]
        self.move_mapping = game_settings["move_mapping"]

    def generate_response(self, total_moves_made: list[list[str]]):
        opt_strategy = rps_optimal_strategy(self.r, self.p, self.s)
    
        # generate random number in [0, 1)
        random_number = random.random()
        if (random_number < opt_strategy[self.move_mapping["rock"]]):
            move = self.move_mapping["rock"]
        elif (random_number < opt_strategy[self.move_mapping["rock"]] + opt_strategy[self.move_mapping["paper"]]):
            move = self.move_mapping["paper"]
        else:
            move = self.move_mapping["scissors"]

        output_text = f"[move] (single-round-equilibrium-player) {move}"

        return {
            "output_text": output_text,
            "input_tokens": 0,
            "output_tokens": len(output_text.split()),
            "total_tokens": len(output_text.split()),
        }
    
class PatternPlayer(Player):
    """
    Represents a pattern player in the chat game.

    Attributes
    ----------
    id : int
        player id, should be 0 or 1
    unique_name : str
        unique name for the player, should be player_{id}
    system_prompt : str
        initial system prompt to start the game
    context : list
        list of chat history
    player_file : str
        path to the player's log file
    context_file : str
        path to the player's context file
    fresh : bool
        whether the player is fresh (True) or not (False) (non-fresh players are experienced players and created with the duplicate() method)
    active : bool
        an active player has already played some rounds against its current opponent
        an inactive player will now play their first round against their current opponent
    pattern : list
        list of moves in the pattern
    """
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
        pattern: list,
    ):
        """
        Parameters
        ----------
        id : int
            player id, should be 0 or 1
        system_prompt : str
            initial system prompt to start the game
        log_dir : str
            path to the log directory of the specific game played
        pattern : list
            list of moves in the pattern
        """
        super().__init__(id, system_prompt, log_dir)
        self.pattern = pattern
        self.pattern_index = 0

    def generate_response(self, total_moves_made: list[list[str]]):
        move = self.pattern[self.pattern_index]
        self.pattern_index = (self.pattern_index + 1) % len(self.pattern)

        output_text = f"[move] (pattern-player) {move}"
        return {
            "output_text": output_text,
            "input_tokens": 0,
            "output_tokens": len(output_text.split()),
            "total_tokens": len(output_text.split()),
        }
    
class AdaptivePlayer(Player):
    """
    Represents a player who uses frequency analysis to adapt to the opponent's moves.
    """
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
        move_mapping: dict,
    ):
        super().__init__(id, system_prompt, log_dir)
        self.move_mapping = move_mapping
        
    def win_to_move(self, move):
        if move == self.move_mapping["rock"]:
            return self.move_mapping["paper"]
        elif move == self.move_mapping["paper"]:
            return self.move_mapping["scissors"]
        else:
            return self.move_mapping["rock"]
        
    def generate_response(self, total_moves_made: list[list[str]]):
        if len(total_moves_made) == 0:
            move = random.choice(list(self.move_mapping.values()))
        else:
            opponent_moves = { k : 0 for k in self.move_mapping.values() }
            for round_moves in total_moves_made:
                opponent_moves[round_moves[1 - self.id]] += 1
            opponent_most_frequent_move = max(opponent_moves, key=opponent_moves.get)
            move = self.win_to_move(opponent_most_frequent_move)
        
        output_text = f"[move] (adaptive-player) {move}"
        return {
            "output_text": output_text,
            "input_tokens": 0,
            "output_tokens": len(output_text.split()),
            "total_tokens": len(output_text.split()),
        }
    
class TitForTatPlayer(AdaptivePlayer):
    """
    Represents a player who counters the opponent's previous move.
    """
    def __init__(
            self,
            id,
            system_prompt,
            log_dir,
            move_mapping : dict,
        ):
        super().__init__(id, system_prompt, log_dir)
        self.move_mapping = move_mapping
        
    def generate_response(self, total_moves_made: list[list[str]]):
        if len(total_moves_made) == 0: 
            move = random.choice(list(self.move_mapping.values()))
        else:
            opponent_move = total_moves_made[-1][1 - self.id]
            move = self.win_to_move(opponent_move)
        
        output_text = f"[move] (tit-for-tat-player) {move}"
        return {
            "output_text": output_text,
            "input_tokens": 0,
            "output_tokens": len(output_text.split()),
            "total_tokens": len(output_text.split()),
        }