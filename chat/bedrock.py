from chat.player import Player

import os
import json

class BedrockChat:
    """
    
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
    """
    def __init__(
        self,
        id: int,
        players: list[Player],
        game_type: str,
        game_settings_type: str,
        log_dir: str,
    ):
        """
        Parameters
        ----------
        id : int
            game id
        players : list
            list of player objects, should have two players
        game_type : str
            type of the game, e.g., "rps", "pd"
        game_settings_type : str
            game settings type
        log_dir : str
            path to the root log directory
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