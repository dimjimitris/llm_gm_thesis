import random

class RockPaperScissorsGame:
    def __init__(self, scoring_rules):
        self.scoring_rules = scoring_rules
        self.moves = ["rock", "paper", "scissors"]
        self.player_scores = [None, None]  # Player 1 and Player 2 scores

    def play_round(self, move1, move2):
        """
        Execute a round of Rock-Paper-Scissors.

        move1: str - Move of player 1
        move2: str - Move of player 2

        Returns a tuple (score1, score2)
        """
        if move1 not in self.moves or move2 not in self.moves:
            raise ValueError("Invalid move. Moves must be 'rock', 'paper', or 'scissors'.")

        if move1 == "rock":
            if move2 == "rock":
                self.player_scores = [
                    self.scoring_rules["tie"],
                    self.scoring_rules["tie"]
                ]
            elif move2 == "paper":
                self.player_scores = [
                    - self.scoring_rules["p"],
                    self.scoring_rules["p"]
                ]
            elif move2 == "scissors":
                self.player_scores = [
                    self.scoring_rules["r"],
                    - self.scoring_rules["r"]
                ]
        elif move1 == "paper":
            if move2 == "rock":
                self.player_scores = [
                    self.scoring_rules["p"],
                    - self.scoring_rules["p"]
                ]
            elif move2 == "paper":
                self.player_scores = [
                    self.scoring_rules["tie"],
                    self.scoring_rules["tie"]
                ]
            elif move2 == "scissors":
                self.player_scores = [
                    - self.scoring_rules["s"],
                    self.scoring_rules["s"]
                ]
        elif move1 == "scissors":
            if move2 == "rock":
                self.player_scores = [
                    - self.scoring_rules["r"],
                    self.scoring_rules["r"]
                ]
            elif move2 == "paper":
                self.player_scores = [
                    self.scoring_rules["s"],
                    - self.scoring_rules["s"]
                ]
            elif move2 == "scissors":
                self.player_scores = [
                    self.scoring_rules["tie"],
                    self.scoring_rules["tie"]
                ]
