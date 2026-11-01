import os
from functools import lru_cache
from urllib.parse import ParseResult, urlencode, urlunparse

import botocore.session
import redis
from botocore.model import ServiceId
from botocore.signers import RequestSigner

from output_models import ReporterOutput

ACCOUNTS_HASH_KEY = "accounts"


class ElastiCacheIAMCredentialProvider(redis.CredentialProvider):
    def __init__(self, username: str, resource_id: str, region: str) -> None:
        self.username = username
        self.resource_id = resource_id
        self.region = region

        session = botocore.session.get_session()
        credentials = session.get_credentials()
        if credentials is None:
            raise RuntimeError("No AWS credentials are available for ElastiCache IAM")

        self.request_signer = RequestSigner(
            ServiceId("elasticache"),
            region,
            "elasticache",
            "v4",
            credentials,
            session.get_component("event_emitter"),
        )

    def get_credentials(self) -> tuple[str, str]:
        auth_url = urlunparse(
            ParseResult(
                scheme="https",
                netloc=self.resource_id,
                path="/",
                query=urlencode({"Action": "connect", "User": self.username}),
                params="",
                fragment="",
            )
        )
        signed_url = self.request_signer.generate_presigned_url(
            {
                "method": "GET",
                "url": auth_url,
                "body": {},
                "headers": {},
                "context": {},
            },
            operation_name="connect",
            expires_in=900,
            region_name=self.region,
        )
        if signed_url is None:
            raise RuntimeError("Failed to generate an ElastiCache IAM auth token")
        return self.username, signed_url.removeprefix("https://")


def _redis_mode() -> str:
    configured_mode = os.getenv("REDIS_MODE")
    if configured_mode is None:
        configured_mode = (
            "elasticache" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "url"
        )
    mode = configured_mode.strip().lower()
    if mode not in {"url", "elasticache"}:
        raise ValueError("REDIS_MODE must be 'url' or 'elasticache'")
    return mode


@lru_cache(maxsize=1)
def _get_redis_client() -> redis.Redis | redis.RedisCluster:
    if _redis_mode() == "elasticache":
        host = os.getenv("ELASTICACHE_HOST")
        username = os.getenv("ELASTICACHE_USERNAME")
        resource_id = os.getenv("ELASTICACHE_RESOURCE_ID")
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if not host or not username or not resource_id or not region:
            raise RuntimeError(
                "ELASTICACHE_HOST, ELASTICACHE_USERNAME, "
                "ELASTICACHE_RESOURCE_ID, and AWS_REGION must be set"
            )

        try:
            port = int(os.getenv("ELASTICACHE_PORT", "6379"))
        except ValueError as error:
            raise ValueError("ELASTICACHE_PORT must be an integer") from error

        cluster_mode = os.getenv("ELASTICACHE_CLUSTER_MODE", "false").lower()
        if cluster_mode not in {"true", "false"}:
            raise ValueError("ELASTICACHE_CLUSTER_MODE must be 'true' or 'false'")

        credentials = ElastiCacheIAMCredentialProvider(
            username=username,
            resource_id=resource_id,
            region=region,
        )
        client_type = redis.RedisCluster if cluster_mode == "true" else redis.Redis
        return client_type(
            host=host,
            port=port,
            credential_provider=credentials,
            ssl=True,
            decode_responses=True,
        )

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL must be set to access reporter data")
    return redis.Redis.from_url(redis_url, decode_responses=True)


def save_reporter_output(output: ReporterOutput) -> None:
    _get_redis_client().hset(
        ACCOUNTS_HASH_KEY,
        output.account.account_name,
        output.model_dump_json(),
    )


def get_reporter_output(account_name: str) -> ReporterOutput | None:
    serialized_output = _get_redis_client().hget(ACCOUNTS_HASH_KEY, account_name)
    if serialized_output is None:
        return None
    return ReporterOutput.model_validate_json(serialized_output)


def get_reporter_outputs() -> list[ReporterOutput]:
    serialized_outputs = _get_redis_client().hgetall(ACCOUNTS_HASH_KEY)
    return [
        ReporterOutput.model_validate_json(serialized_output)
        for _, serialized_output in sorted(serialized_outputs.items())
    ]
