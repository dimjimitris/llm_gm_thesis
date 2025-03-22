from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PlayerRole,
)

import os
import json
import boto3

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
        model_id : str
            bedrock model id
        temp : float
            temperature parameter for sampling
        max_tokens : int
            maximum number of tokens to generate
        """
        self.id = id
        self.unique_name = f"player_{self.id}"
        self.system_prompt = system_prompt
        self.context = list()

        os.makedirs(log_dir, exist_ok=True)
        self.player_file = os.path.join(log_dir, f"{self.unique_name}.log")
        self.context_file = os.path.join(log_dir, f"{self.unique_name}.json")

        self.fresh = True
        self.active = False

        self.temp = temp
        self.max_tokens = max_tokens
        self.model_id = model_id

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
            "content": self._content_wrapper(content)
        }

        if len(self.context) == 0:
            self.context.append(entry)
            return
        
        last_entry = self.context[-1]
        if last_entry["role"] == entry["role"]:
            last_entry_text = self._content_unwrapper(last_entry["content"])
            entry_text = self._content_unwrapper(entry["content"])
            # if the entry_text has a tag, remove it
            if entry_text.startswith("[hint] ") or entry_text.startswith("[move] "):
                entry_text = entry_text[7:]
            elif entry_text.startswith("[hint]") or entry_text.startswith("[move]"):
                entry_text = entry_text[6:]
            last_entry["content"] = self._content_wrapper(f"{last_entry_text}\n{entry_text}")
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
            messages=self.context,
            system=self._system_prompt_wrapper(self.system_prompt),
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
    
    def _system_prompt_wrapper(self, system_prompt: str):
        return [{ "text" : system_prompt }]

    def _content_wrapper(self, content: str):
        return [{ "text" : content }]

    def _content_unwrapper(self, content: str):
        return content[0]["text"]