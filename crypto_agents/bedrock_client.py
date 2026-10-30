import os

from aws_bedrock_token_generator import provide_token
from openai import AsyncOpenAI


def create_bedrock_client() -> AsyncOpenAI:
    project_id = os.getenv("PROJECT_ID")
    bedrock_base_url = os.getenv("AWS_BEDROCK_BASE_URL")

    if not project_id or not bedrock_base_url:
        raise ValueError("PROJECT_ID and AWS_BEDROCK_BASE_URL must be set")

    return AsyncOpenAI(
        api_key=provide_token(),
        base_url=bedrock_base_url,
        project=project_id,
    )
