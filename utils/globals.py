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

# game identifiers
class GameId(Enum):
    NEGOTIATION = 0
    DICTATOR = 1
    ROCK_PAPER_SCISSORS = 2

# agent roles
class AgentRole(Enum):
    SYSTEM = "system"           # bedrock models do not use this role in requests, they instead accept a seperate system prompt
    ASSISTANT = "assistant"     # the assistant role is used to provide the user with information or guidance (basically, this is the LLM player that is actively playing)
    USER = "user"               # the user role is used to represent the user in the game (basically, this is the LLM player that is the opponent of the assistant)