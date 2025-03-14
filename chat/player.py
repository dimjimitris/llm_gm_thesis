import os
import json

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
    """
    def __init__(
        self,
        id: int,
        system_prompt: str,
        log_dir: str,
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

    def load_context(self) -> None:
        """
        loads the player's context from the context log file
        """
        with open(self.context_file, "r") as f:
            self.context = json.load(f)

    def save_context(self) -> None:
        """
        saves the player's context to the context log file
        """
        with open(self.context_file, "a+") as f:
            # if context file is not empty, it contains a list of dictionaries
            # so we need to put the current context entries in this list
            context = json.load(f) if os.path.getsize(self.context_file) > 0 else []
            context.extend(self.context)
            f.seek(0)
            json.dump(context, f, indent=2)

    def append_context(self, entry: dict) -> None:
        """
        appends the context to the player's context

        Parameters
        ----------
        entry : dict
            context entry to append to the player's context
        """
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

    def _content_wrapper(self, content: str):
        return [{ "text" : content }]

    def _content_unwrapper(self, content: str):
        return content[0]["text"]