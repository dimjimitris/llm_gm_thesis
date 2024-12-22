from utils.funcs import content_wrapper
import os

class Game:
    def __init__(
        self,
        id : int,
        game_type : str,
        prompt_path : str,
        log_path : str,
    ):
        self.id = id
        self.game_type = game_type
        self.unique_name = f"{self.game_type}_{self.id}"
        self.prompt_path = prompt_path
        self.log_path = os.path.join(log_path, f"{self.unique_name}")
        # if the log path doesn't exist, create it
        if not os.path.exists(self.log_path):
            os.makedirs(name=self.log_path)
        

    def _content_wrapper(self, content : str):
        return content_wrapper(content)
    
    def _log(self, log_path, text : str, newline : bool = False):
        with open(log_path, "a") as f:
            f.write(text + ("\n" if newline else ""))

    
