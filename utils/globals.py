from dotenv import load_dotenv
import os
from enum import Enum

# load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")          # These keys are needed
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")  # to access the LLM API

# check if environment variables are set
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in a .env file")

class PlayerRole(Enum):
    """
    Enum class for player roles

    Attributes
    ----------

    ASSISTANT : str
        the assistant role is the LLM player that is currently playing. It provides the user with its answers.
    USER : str
        the user role is used to represent the user in the game. It provides the assistant with information on its opponent and also provides the assistant with hints on how to play the game.
    """
    ASSISTANT = "assistant"
    USER = "user"