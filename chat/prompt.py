class PromptGenerator:
    """
    A class to generate properly formatted prompts for the chat game.

    Attributes
    ----------
    system_prompt : str
        system prompt for the game
    """
    def __init__(
        self,
        game_type: str,
        game_settings: dict,
        system_prompt_skeleton: str,
    ):
        """
        Parameters
        ----------
        game_type : str
            type of the game, e.g., "rps"
        game_settings : dict
            dictionary containing game settings
        system_prompt_skeleton : str
            skeleton of the system prompt for the game to be played
        """
        if game_type == "rps":
            self.system_prompt = self._generate_prompt_rps(system_prompt_skeleton, game_settings)

    def _generate_prompt_rps(self, system_prompt_skeleton: str, game_settings: dict) -> str:
        """
        Generates a system prompt for the game to be played.

        Parameters
        ----------
        system_prompt_skeleton : str
            skeleton of the system prompt for the game to be played
        game_settings : dict
            dictionary containing game settings

        Returns
        -------
        str
            system prompt for the Rock-Paper-Scissors game
        """
        r = game_settings["r"]
        p = game_settings["p"]
        s = game_settings["s"]
        move_mapping : dict = game_settings["move_mapping"]
        
        return system_prompt_skeleton.format(
            rock=move_mapping["rock"],
            paper=move_mapping["paper"],
            scissors=move_mapping["scissors"],
            r=r,
            p=p,
            s=s,
        )
    
    def get_prompt(self) -> str:
        """
        Returns the system prompt for the game.

        Returns
        -------
        str
            system prompt for the game
        """
        return self.system_prompt
