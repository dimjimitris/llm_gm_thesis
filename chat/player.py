from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PlayerRole,
)

from utils.rps import (
    optimal_strategy as rps_optimal_strategy,
)

from utils.pd import (
    optimal_strategy as pd_optimal_strategy,
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
    player_type : str
        type of the player
    """
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
        player_type : str,
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
        player_type : str
            type of the player
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
        self.player_type = player_type

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
        with open(self.context_file, "w") as f:
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
        player_type : str,
        k : int,
        model_id: str,
        temp: float,
        max_tokens: int,
        thinking: bool,
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
        player_type : str
            type of the player
        k : int
            number of responses to generate for ToT evaluation
        model_id : str
            bedrock model id
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        """
        super().__init__(id, system_prompt, log_dir, player_type, k)

        self.temp = temp
        self.max_tokens = max_tokens
        self.model_id = model_id
        self.thinking = thinking

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

        if self.thinking:
            response = client.converse(
                modelId=self.model_id,
                messages=self.context,
                system=BedrockPlayer._system_prompt_wrapper(self.system_prompt),
                inferenceConfig=inference_config,
                additionalModelRequestFields={
                    "thinking" : {
                        "type": "enabled",
                        "budget_tokens": self.max_tokens // 5 * 4,  # 80% of max_tokens for thinking,
                    },
                },
            )
        else:
            response = client.converse(
                modelId=self.model_id,
                messages=self.context,
                system=BedrockPlayer._system_prompt_wrapper(self.system_prompt),
                inferenceConfig=inference_config,
                #additionalModelRequestFields={
                #    "thinking" : {
                #        "type": "enabled",
                #        "budget_tokens": self.max_tokens // 5 * 4,  # 80% of max_tokens for thinking,
                #    },
                #},
            )

        #print(f"{self.player_file} Response: {response}")
        # format json response
        #import json
        #print(f"{self.player_file} Response: {json.dumps(response, indent=2)}")

        output_list : list[dict] = response["output"]["message"]["content"]

        thinking_text, reasoning_text, output_text = None, None, None
        # if output_list length is > 1, then thinking is enabled, add this check later
        for item in output_list:
            if "type" in item and item["type"] == "thinking":
                thinking_text = item["thinking"]
            elif "text" in item:
                output_text = item["text"]
            elif "reasoningContent" in item:
                reasoning_text = item["reasoningContent"]["reasoningText"]["text"]

        #if reasoning_text is not None and output_text is not None:
        #    #output_text =f"Reasoning:\n{reasoning_content}\n\nFinal Answer:\n{ttext}"
        #    output_text = output_text
        #elif output_text is not None:
        #    output_text = output_text
        #elif reasoning_text is not None:
        #    #output_text = f"Reasoning:\n{reasoning_content}"
        #    output_text = "[ERROR] No response generated."
        #else:
        #    output_text = "[ERROR] No response generated."
        if output_text is None:
            output_text = "[ERROR] No response generated."
        
        usage = response["usage"]

        #print(f"{self.system_prompt}")
        print(f"{self.player_file}: Thinking: {thinking_text}\nReasoning: {reasoning_text}\nFinal Answer: {output_text}\n")

        return {
            "output_text": output_text,
            "thinking_text": thinking_text,
            "reasoning_text": reasoning_text,
            "input_tokens": int(usage["inputTokens"]),
            "output_tokens": int(usage["outputTokens"]),
            "total_tokens": int(usage["totalTokens"]),
        }
    
    def copy(self, idx : int) -> "BedrockPlayer":
        new_player = BedrockPlayer(
            10*(idx + 1) + self.id,
            self.system_prompt,
            self.log_dir,
            self.player_type,
            1,
            self.model_id,
            self.temp,
            self.max_tokens,
            self.thinking,
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
        super().__init__(id, system_prompt, log_dir, "srep")
        self.ac = game_settings["ac"]
        self.ba = game_settings["ba"]
        self.cb = game_settings["cb"]
        self.a = game_settings["a"]
        self.b = game_settings["b"]
        self.c = game_settings["c"]

    def generate_response(self, total_moves_made: list[list[str]]):
        opt_strategy = rps_optimal_strategy(self.ac, self.ba, self.cb)
    
        # generate random number in [0, 1)
        random_number = random.random()
        if (random_number < opt_strategy["a"]):
            move = self.a
        elif (random_number < opt_strategy["a"] + opt_strategy["b"]):
            move = self.b
        else:
            move = self.c

        output_text = f"[move] (single-round-equilibrium-player) {move}"

        return {
            "output_text": output_text,
            "input_tokens": 0,
            "output_tokens": len(output_text.split()),
            "total_tokens": len(output_text.split()),
        }
    
class SrepPD(Player):
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
        super().__init__(id, system_prompt, log_dir, "srep")
        self.aa = game_settings["aa"]
        self.ab = game_settings["ab"]
        self.ba = game_settings["ba"]
        self.bb = game_settings["bb"]
        self.a = game_settings["a"]
        self.b = game_settings["b"]

    def generate_response(self, total_moves_made: list[list[str]]):
        opt_strategy = pd_optimal_strategy(self.aa, self.ab, self.ba, self.bb)
    
        # generate random number in [0, 1)
        random_number = random.random()
        if (random_number < opt_strategy["a"]):
            move = self.a
        else:
            move = self.b

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
        super().__init__(id, system_prompt, log_dir, "pp")
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
        game_settings: dict,
        player_type : str = "ap",
    ):
        super().__init__(id, system_prompt, log_dir, player_type)
        self.game_settings = game_settings
        
    def win_to_move(self, move):
        if move == self.game_settings["a"]:
            return self.game_settings["b"]
        elif move == self.game_settings["b"]:
            return self.game_settings["c"]
        else:
            return self.game_settings["a"]
        
    def generate_response(self, total_moves_made: list[list[str]]):
        if len(total_moves_made) == 0:
            moves = []
            if "a" in self.game_settings:
                moves.append(self.game_settings["a"])
            if "b" in self.game_settings:
                moves.append(self.game_settings["b"])
            if "c" in self.game_settings:
                moves.append(self.game_settings["c"])

            move = random.choice(moves)
        else:
            opponent_moves = {}
            if "a" in self.game_settings:
                opponent_moves[self.game_settings["a"]] = 0
            if "b" in self.game_settings:
                opponent_moves[self.game_settings["b"]] = 0
            if "c" in self.game_settings:
                opponent_moves[self.game_settings["c"]] = 0

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

class MaximizerFreqP(Player):
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
        game_settings: dict,
        player_type : str = "mf",
    ):
        super().__init__(id, system_prompt, log_dir, player_type)
        self.game_settings = game_settings
        
    def win_to_move(self, move):
        if move == self.game_settings["a"]:
            if self.game_settings["ba"] > self.game_settings["aa"]:
                return self.game_settings["b"]
            else:
                return self.game_settings["a"]
        elif move == self.game_settings["b"]:
            if self.game_settings["bb"] > self.game_settings["ab"]:
                return self.game_settings["b"]
            else:
                return self.game_settings["a"] 
        
    def generate_response(self, total_moves_made: list[list[str]]):
        if len(total_moves_made) == 0:
            moves = []
            if "a" in self.game_settings:
                moves.append(self.game_settings["a"])
            if "b" in self.game_settings:
                moves.append(self.game_settings["b"])
            if "c" in self.game_settings:
                moves.append(self.game_settings["c"])

            move = random.choice(moves)
        else:
            opponent_moves = {}
            if "a" in self.game_settings:
                opponent_moves[self.game_settings["a"]] = 0
            if "b" in self.game_settings:
                opponent_moves[self.game_settings["b"]] = 0
            if "c" in self.game_settings:
                opponent_moves[self.game_settings["c"]] = 0

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
            game_settings : dict,
        ):
        super().__init__(id, system_prompt, log_dir, game_settings, "tft")
        
    def generate_response(self, total_moves_made: list[list[str]]):
        if len(total_moves_made) == 0: 
            moves = []
            if "a" in self.game_settings:
                moves.append(self.game_settings["a"])
            if "b" in self.game_settings:
                moves.append(self.game_settings["b"])
            if "c" in self.game_settings:
                moves.append(self.game_settings["c"])
                
            move = random.choice(moves)
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
    
class TftPD(MaximizerFreqP):
    def __init__(
            self,
            id,
            system_prompt,
            log_dir,
            game_settings: dict,
        ):
        super().__init__(id, system_prompt, log_dir, game_settings, "tft")

    def generate_response(self, total_moves_made: list[list[str]]):
        if len(total_moves_made) == 0: 
            moves = []
            if "a" in self.game_settings:
                moves.append(self.game_settings["a"])
            if "b" in self.game_settings:
                moves.append(self.game_settings["b"])
            if "c" in self.game_settings:
                moves.append(self.game_settings["c"])

            move = random.choice(moves)
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