# Probing LLM Counterfactual Reasoning in Game Theory

This repository contains the codebase for the diploma thesis *"Probing LLM Counterfactual Reasoning in Game Theory"* of the author. That work takes a deeper look into reasoning abilities of Large Language Models in Games; discussing their emergency and techniques to trigger them. It establishes performance metrics for agents in Games.

## Author
Dimitrios Georgousis, Electrical and Computer Engineer at NTUA (MEng)

## Overview

Simultaneous-move, symmetric games are used in experimentation- Prisoner’s Dilemma, Stag Hunt, and Rock-Paper-Scissors- which offer parameterization opportunities by adjusting both naming schemes of moves offered to players and payoffs of said moves. LLMs are likely to be aware of only the typical or usual setting of each game; therefore, counterfactual settings (settings created from parameter modification) serve as a test of LLM flexibility and sensitivity to changes in payoff structure, and as juxtaposition of strategic thinking and reliance to prior knowledge, LLMs might have on the default setting of the games.

A well-known method for targeting LLM thinking abilities towards specific tasks is the employment of advanced prompting techniques. In this work, a range of prompting strategies, including Zero-Shot, Chain-of-Thought, and Solo-Performance Prompting, are used; experiments are also performed on their Self-Consistency counterparts. These techniques reflect an attempt to elicit more deliberate and context-aware responses from the models. They aim to minimize the influence of surface-level pattern matching and instead encourage reasoning that takes into account the specific parameters of each game instance.

To evaluate the presence of strategic reasoning, LLMs are compared against non-AI players, who follow specific preset strategies, and against themselves following different prompt styles. This comparative framework allows for an assessment of whether LLMs adapt their play in a manner consistent with rational strategic behavior, or if their responses merely reflect superficial cues from the prompt. Key indicators include responsiveness to opponent strategy, exploitation of opponent tendencies, and behavioral shifts across repeated rounds. In particular, repeated interactions offer a unique window into whether LLMs can exhibit conditional cooperation, retaliatory strategies, or learning-like behavior over time.

By systematically varying both the game settings and the prompting techniques, this thesis aims to uncover the conditions under which LLMs demonstrate behavior indicative of genuine strategic reasoning. The f indings contribute to the broader understanding of LLM capabilities, especially in dynamic decision-making contexts, and highlight both the promise and limitations of current models in replicating human-like strategic thought.


## Project Structure

```
.
├── README.md
├── analysis
│   ├── analysis_1.ipynb
│   ├── analysis_2.ipynb
│   ├── analysis_3_pd.ipynb
│   ├── analysis_3_rps.ipynb
│   └── analysis_4.ipynb
├── chat
│   ├── bedrock.py
│   ├── pd.py
│   ├── player.py
│   ├── prompt.py
│   └── rps.py
├── descriptions
│   ├── pd.py
│   └── rps.py
│── utils
│   ├── globals.py
│   ├── pd.py
│   └── rps.py
├── play.py
├── play_pd.py
├── logs
├── logs_pd
├── requirements.txt
```

## Key Features

- Gym-like modular and adaptable environment for experimentation
- Experimental study across strategic games and various counterfactuals thereof
- Analysis of game parameterization and prompting technique in LLM performance
- Comparison of modern LLMs provided via BedRock
- Use of simple analytic metrics that provide robust results

## Games

The framework supports integration of:
- 2-player repeated games: Prisoner's Dilemma, Stag Hunt & Rock-Paper-Scissors

## Installation

### System Prerequisites

```
$ python3 --version
Python 3.12.3
$ git --version
git version 2.43.0
```

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. venv prerequisites:
   ```
   (venv) $ python --version
   Python 3.12.3
   (venv) $ pip --version
   pip 25.0.1 from /some/directory (python 3.12)
   ```

4. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

   If `requirements.txt` doesn't exist, create it with the following content:
   ```
   boto3
   numpy
   pandas
   python-dotenv
   tabulate
   ```

5. Set up environment variables:
   - Create a `.env` file in the root directory of the project
   - Add your BedRock API key to the `.env` file:
     ```
     AWS_ACCESS_KEY_ID = your_aws_access_key_id_here
     AWS_SECRET_ACCESS_KEY = your_aws_secret_access_key_here
     ```

6. If there are any additional data files or models required, place them in the appropriate directories within the project structure.

### Note

This project uses environment variables to manage sensitive information like API keys. Never commit your `.env` file or share your API keys publicly.

## Usage

### Running experiments on Prisoner's Dilemma or Stag Hunt

The file `play_pd.py` contains example usages of our environment in organising experiments. You may use it as is or perform changes to your needs.

```bash
python play_pd.py
```

### Running experiments on Rock-Paper-Scissors

The file `play.py` contains example usages of our environment in organising experiments. You may use it as is or perform changes to your needs.

```bash
python play.py
```

## Game-Description Structure

The `descriptions` directory contains game descriptions organized as follows:

Let's take a look at `pd.py`, which refers to Prisoner's Dilemma (and Stag Hunt). Similar things are true for Rock-Paper-Scissors.

- strings `PD_INIT_{ZS,SPP,COT}` refer to the initialization prompt provided to LLM agents as a *system* prompt.
- dictionary `PD_SETTINGS_COLLECTION` refers to various game settings that can be used for experimentation. These will take the place of the placeholder values that appear in the initialization prompts mentioned previously.

## Logs

- `logs_pd/logs_3` is used for results of Prisoner's Dilemma (and Stag Hunt)
- `logs/logs_3` is used for results of Rock-Paper-Scissors. `logs/logs_{1,2}` refer to experimental results used in early experimentation relevant to preliminary work of the thesis project.

## Main Findings

This thesis studied how large language models (LLMs) and large reasoning models (LRMs) behave in game-theoretic settings like Prisoner’s Dilemma and Rock-Paper-Scissors. We tested different models, prompt styles, and opponents to examine cooperation, adaptation, and rationality.

Key findings:

* LLMs often show cooperative behavior in repeated games, aiming for mutual benefit rather than self-interest.
* In Rock-Paper-Scissors, irrational biases in move selection fade with repeated play, and LLMs approach equilibrium strategies when given history.
* Larger models sometimes overthink simple tasks, while smaller models performed better with structured prompting. Larger models excelled in more complex reasoning tasks.
* Against vindictive players (more specifically the 'Tit-for-Tat' player in the above work), LLMs refined strategies over time, showing dynamic adaptation.
* Prompt style strongly influenced results: structured prompts improved smaller models, while added complexity sometimes hindered larger ones.
* “Thinking” variants showed mixed results - stronger in reasoning tasks but also more error-prone (e.g., confusion).
* Counterfactual reasoning worked well for most models, with only older/smaller ones struggling more noticeably.

Overall, LLMs can act strategically and cooperatively when prompted well, but outcomes depend on game type, opponent, prompt design, and model scale.


## Future Work

This thesis showed that LLMs can adapt strategically in games, but several questions remain:

* Humans vs. LLMs: Study alignment, persuasion, and trust when people play against LLMs.
* Multi-agent games with communication: Explore negotiation, signaling, and strategic use of language.
* Scaling with model size: Investigate when larger models help or hinder decision-making.
* Longer games & memory: Test if LLMs can form lasting strategies using memory or extended play.
* Benchmarks for rationality: Develop standardized ways to measure cooperation, adaptation, and reasoning.

Overall, LLMs show promise as strategic agents, but more research is needed to test their limits, durability, and generalizability.


## Contact
For further information, please reach out to dimitrisgeor01@gmail.com.
