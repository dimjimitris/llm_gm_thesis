from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

import os
import boto3
import json

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
        return [
            {
                "type": "text",
                "text": content,
            }
        ]
    
    def _log(self, log_path, text : str, newline : bool = False):
        with open(log_path, "a") as f:
            f.write(text + ("\n" if newline else ""))

    def _generate_response(
        self,
        context, # messages
        log_agent_path,
        system_prompt,
        temperature,
        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens = 200,
    ) -> str:

        #system_prompt = context[0]['content'][0]['text']
        #context[0] = {
        #    "role" : "user",
        #    "content" : [
        #        {
        #            "type" : "text",
        #            "text" : "Let's play the game described in the system prompt.\n"
        #        }
        #    ]
        #}
        messages = context

        bedrock_runtime_client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name="us-west-2",
        )

        payload = {
            "system" : system_prompt,
            "messages" : messages,
            "max_tokens" : max_tokens,
            "anthropic_version" : "bedrock-2023-05-31",
        }

        response = bedrock_runtime_client.invoke_model(
            body=json.dumps(payload),
            modelId=model_id,
        )

        output_binary = response["body"].read()
        output_json = json.loads(output_binary)
        output = output_json["content"][0]["text"]

        self._log(log_agent_path, output, newline=True)

        return output