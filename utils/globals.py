from dotenv import load_dotenv
import os
from enum import Enum

# model id, set during game initialization
MODEL_ID = None

# load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# check if environment variables are set
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in a .env file")

# game identifiers
class GameId(Enum):
    NEGOTIATION = 0
    DICTATOR = 1
    ROCK_PAPER_SCISSORS = 2

# game id, set during game initialization
GAME_ID = None

# agent roles
class AgentRole(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"