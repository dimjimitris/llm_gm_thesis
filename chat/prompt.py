from descriptions.rps import RPS_DESC

INITIAL_PROMPT : str = RPS_DESC["init"]

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
    ):
        """
        Parameters
        ----------
        game_type : str
            type of the game, e.g., "rps"
        game_settings : dict
            dictionary containing game settings
        """
        if game_type == "rps":
            self.system_prompt = self._generate_prompt_rps(game_settings)

    def _generate_prompt_rps(self, game_settings: dict) -> str:
        """
        Generates a system prompt for the Rock-Paper-Scissors game.

        Parameters
        ----------
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
        
        return INITIAL_PROMPT.format(
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
