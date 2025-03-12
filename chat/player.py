import os
import json

class Player:
    """
    represents a player in the chat game keeps player's log and context history

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
    player_log : str
        path to the player's log file
    context_log : str
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
        game_type: str,
        game_id: int,
        log_path: str,
    ) -> None:
        """
        Parameters
        ----------
        id : int
            player id, should be 0 or 1
        system_prompt : str
            initial system prompt to start the game
        game_type : str
            type of the game, e.g., "rps"
        game_id : int
            game id
        log_path : str
            path to the root log directory
        """
        self.id = id
        self.unique_name = f"player_{self.id}"
        self.system_prompt = system_prompt
        self.context = list()

        game_unique_name = f"{game_type}_{game_id}"
        log_path_aux = os.path.join(log_path, game_type, game_unique_name)

        os.makedirs(log_path_aux, exist_ok=True)
        self.player_log = os.path.join(log_path_aux, f"{self.unique_name}.log")
        self.context_log = os.path.join(log_path_aux, f"{self.unique_name}.context")

        self.fresh = True
        self.active = False

    def duplicate(
        self,
        id: int,
        system_prompt: str,
        game_type: str,
        game_id: int,
        log_path: str,
    ) -> "Player":
        """
        creates a duplicate player object. All parameters of duplicate() refer to the target player. duplicate() duplicates information of the source player (self) to the target player.

        Parameters
        ----------
        id : int
            player id, should be 0 or 1
        system_prompt : str
            initial system prompt to start the game
        game_type : str
            type of the game, e.g., "rps"
        game_id : int
            game id
        log_path : str
            path to the root log directory

        Returns
        -------
        Player
            target player object
        """
        target_player = Player(id, system_prompt, game_type, game_id, log_path)

        with open(self.player_log, "r") as f1, open(target_player.player_log, "w") as f2:
            f2.write(f1.read())
        with open(self.context_log, "r") as f1, open(target_player.context_log, "w") as f2:
            f2.write(f1.read())
        with open(target_player.context_log, "r") as f:
            target_player.context = json.load(f)
        
        target_player.fresh = False
        return target_player

    def save_context(self) -> None:
        """
        saves the player's context to the context log file
        """
        with open(self.context_log, "w") as f:
            json.dump(self.context, f)

    def load_context(self) -> None:
        """
        loads the player's context from the context log file
        """
        with open(self.context_log, "r") as f:
            self.context = json.load(f)

    def append_context(self, entry: dict) -> None:
        """
        appends the context to the player's context

        Parameters
        ----------
        context : dict
            context to append
        """
        if len(self.context) == 0:
            self.context.append(entry)
            return
        
        last_entry = self.context[-1]
        if last_entry["role"] == entry["role"]:
            last_entry_text = self._content_unwrapper(last_entry["content"])
            entry_text = self._content_unwrapper(entry["content"])
            last_entry["content"] = self._content_wrapper(f"{last_entry_text}\n{entry_text}")
        else:
            self.context.append(entry)

    def _content_wrapper(self, content: str):
        return [{ "text" : content }]

    def _content_unwrapper(self, content: str):
        return content[0]["text"]

    def append_log(self, log: str) -> None:
        """
        appends the log to the player's log

        Parameters
        ----------
        log : str
            log to append
        """
        with open(self.player_log, "a") as f:
            f.write(log)

