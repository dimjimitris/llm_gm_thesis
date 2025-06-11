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
            self.system_prompt = PromptGenerator._generate_prompt_rps(
                system_prompt_skeleton, 
                game_settings,
            )
        elif game_type == "pd":
            self.system_prompt = PromptGenerator._generate_prompt_pd(
                system_prompt_skeleton, 
                game_settings,
            )
        else:
            raise ValueError(f"Unknown game type: {game_type}")

    @staticmethod
    def _generate_prompt_rps(system_prompt_skeleton: str, game_settings: dict) -> str:
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
        a = game_settings["a"]
        b = game_settings["b"]
        c = game_settings["c"]
        ac = game_settings["ac"]
        ba = game_settings["ba"]
        cb = game_settings["cb"]
        
        return system_prompt_skeleton.format(
            a=a,
            b=b,
            c=c,
            ac=ac,
            ba=ba,
            cb=cb,
        )
    
    @staticmethod
    def _generate_prompt_pd(system_prompt_skeleton: str, game_settings: dict) -> str:
        a = game_settings["a"]
        b = game_settings["b"]
        aa = game_settings["aa"]
        bb = game_settings["bb"]
        ab = game_settings["ab"]
        ba = game_settings["ba"]
        return system_prompt_skeleton.format(
            a=a,
            b=b,
            aa=aa,
            bb=bb,
            ab=ab,
            ba=ba,
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
