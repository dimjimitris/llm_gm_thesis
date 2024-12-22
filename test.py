import games.dictator as d
import games.negotiation as n
import games.rockpaperscissors as rps

import boto3

def test_negotiation():
    game = n.NegotiationGame(
        {"book" : 1, "hat" : 2, "ball" : 3},
        [
            {"book" : 1, "hat" : 3, "ball" : 1},
            {"book" : 2, "hat" : 1, "ball" : 2}
        ],
        "semi"
    )
    
    result = game.play()
    return result

def x():
    return

if __name__ == "__main__":
    #game_output = test_negotiation()
#
    #print(game_output["is_valid_deal"])
    bedrock = boto3.client(
        service_name='bedrock',
        region_name='us-west-2',    
    )

    print(bedrock.list_foundation_models())