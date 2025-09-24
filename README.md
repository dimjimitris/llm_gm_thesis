# Probing LLM Counterfactual Reasoning in Game Theory

This repository contains the codebase for the diploma thesis *"Probing LLM Counterfactual Reasoning in Game Theory"* of the author. That work takes a deeper look into reasoning abilities of Large Language Models in Games; discussing their emergency and techniques to trigger them. It establishes performance metrics for agents in Games.

## Author
Dimitrios Georgousis, Electrical and Computer Engineering at NTUA

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

3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

   If `requirements.txt` doesn't exist, create it with the following content:
   ```
   openai
   pandas
   tqdm
   pydantic
   python-dotenv
   ```

4. Set up environment variables:
   - Create a `.env` file in the root directory of the project
   - Add your OpenAI API key to the `.env` file:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

5. If there are any additional data files or models required, place them in the appropriate directories within the project structure.

### Troubleshooting

- If you encounter issues with the OpenAI API, ensure your API key is correctly set in the `.env` file and that you have sufficient credits.
- For any import errors, make sure all required packages are installed and that you're running Python from the correct virtual environment.
- If you face issues with file paths, check that you're running the scripts from the root directory of the project.

### Note

This project uses environment variables to manage sensitive information like API keys. Never commit your `.env` file or share your API keys publicly.

## Usage

### Running Division Game Experiments

To run experiments with bargaining games:

```bash
python run_exps_division_game.py
```

### Running a Single Division Game

To run a single division game:

```bash
python run_division_game.py
```

### Running Table Games

To run table games:

```bash
python run_table_game.py
```

## Prompt Structure

The `prompts` directory contains language-specific prompts organized as follows:

- `agent/`: Contains prompts for agent behavior, memory updates, etc.
  - `memory_update.txt`: Prompt for updating agent's memory after current round (not for bargaining)
  - `emotions/`: Folder with prompts for questioning emotions and inserting them into memory
  - `game_settings/`: Folder with prompts for defining environment, conditions, and general prompt for initialization memory of agent - `outer_emotions/`: Folder with prompts for questioning what emotions to demonstrate and how to describe them to coplayer (not for bargaining)
- `emotions/`: Descriptions for initial agents' emotions
- `games/`: Game-specific prompts and rules
  - `rewards.json`: Reward matrix
  - `rules1.txt`: Rules described for the first player
  - `rules2.txt`: Rules described for the second player

## Languages

Games are currently available in English & Russian. The `{language}` in the directory structure is the chosen language's lowercase name (english, russian).

## Main Findings

1. Emotions significantly alter LLM decision-making, regardless of alignment strategies.
2. GPT-4 shows less alignment with human emotions but breaks alignment in 'anger' mode.
3. GPT-3.5 and Claude demonstrate better alignment with human emotional responses.
4. Proprietary models outperform open-source and uncensored LLMs in decision optimality.
5. Medium-size models show better alignment with human behavior.
6. Adding emotions helps model cooperation and coordination during games.

## Future Work

- Validate findings with both proprietary and open-source LLMs
- Explore finetuning of open-source models on emotional prompting
- Investigate multi-agent approaches for dynamic emotions
- Study the impact of emotions on strategic interactions in short- and long-term horizons


## Contributing

We welcome contributions to this project! If you're interested in contributing, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Citation
Please cite our work as:
> Mozikov, Mikhail, et al. "EAI: Emotional Decision-Making of LLMs in Strategic Games and Ethical Dilemmas." The Thirty-eighth Annual Conference on Neural Information Processing Systems.

## Contact
For further information, please reach out to mozikov@airi.net.

Stay tuned for the code release post-conference!