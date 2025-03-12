from utils.globals import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

import os
import random
import boto3

bedrock = boto3.client(
    service_name='bedrock',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='us-west-2',
)

print(bedrock.list_foundation_models())