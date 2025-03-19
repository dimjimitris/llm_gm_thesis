from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

import os
import random
import boto3

#bedrock = boto3.client(
#    service_name='bedrock',
#    aws_access_key_id=AWS_ACCESS_KEY_ID,
#    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#    region_name='us-west-2',
#)
#
#print(bedrock.list_foundation_models())

def main(s : str):
    # create a boto3 client for the LLM API
    client = boto3.client(
        "bedrock-runtime",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-west-2",
    )

    inference_config = {
        "maxTokens": 512,
        "temperature": 0.8,
    }

    # if s does not end with a newline, add one
    if not s.endswith("\n"):
        s += "\n"

    response = client.converse(
        modelId="us.meta.llama3-3-70b-instruct-v1:0",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": s,
                    }
                ]
            }
        ],
        inferenceConfig=inference_config,
    )

    output_text = response["output"]["message"]["content"][0]["text"]

    print(output_text)

import re

if __name__ == "__main__":
    # read the input
    s = input("Enter a prompt: ")
    main(s)
    #msg = "[move] (scissors|paper|rocck) rock"
#
    #msg_aux = msg.lower().strip()
    #pattern = r'\[move\](?: \(([^)]+)\))? (rock|paper|scissors)'
    #matches = re.findall(pattern, msg_aux)
    #
    #print(matches[0][-1])