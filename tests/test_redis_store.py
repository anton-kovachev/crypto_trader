import os
import unittest
from unittest.mock import Mock, patch, sentinel

from output_models import AccountOutput, ReporterOutput
from output_models.reporter import AccountHoldingSnapshot
from redis_store import (
    ACCOUNTS_HASH_KEY,
    get_reporter_output,
    get_reporter_outputs,
    save_reporter_output,
    _get_redis_client,
    ElastiCacheIAMCredentialProvider,
)


class FakeRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, str]] = {}

    def hset(self, name: str, key: str, value: str) -> None:
        self.hashes.setdefault(name, {})[key] = value

    def hget(self, name: str, key: str) -> str | None:
        return self.hashes.get(name, {}).get(key)

    def hgetall(self, name: str) -> dict[str, str]:
        return self.hashes.get(name, {}).copy()


def make_report(
    account_name: str,
    total_holding_value: float,
) -> ReporterOutput:
    return ReporterOutput(
        account=AccountOutput(
            account_name=account_name,
            holdings=[],
            total_holding_values_time_series=[
                AccountHoldingSnapshot(
                    total_holding_value_in_usdc=total_holding_value,
                    total_holding_value_in_btc=0,
                    timestamp="2026-01-01T00:00:00",
                )
            ],
            logs=[],
            transactions=[],
        ),
        error_message=None,
    )


class RedisStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.redis = FakeRedis()
        self.client_patch = patch(
            "redis_store._get_redis_client",
            return_value=self.redis,
        )
        self.client_patch.start()
        self.addCleanup(self.client_patch.stop)

    def test_saves_json_report_and_replaces_account_field(self) -> None:
        first_report = make_report("account-a", 100)
        updated_report = make_report("account-a", 125)

        save_reporter_output(first_report)
        save_reporter_output(updated_report)

        self.assertEqual(list(self.redis.hashes), [ACCOUNTS_HASH_KEY])
        self.assertEqual(len(self.redis.hashes[ACCOUNTS_HASH_KEY]), 1)
        self.assertEqual(get_reporter_output("account-a"), updated_report)

    def test_lists_reports_sorted_by_account_name(self) -> None:
        save_reporter_output(make_report("account-b", 200))
        save_reporter_output(make_report("account-a", 100))

        self.assertEqual(
            [report.account.account_name for report in get_reporter_outputs()],
            ["account-a", "account-b"],
        )


class RedisConnectionTests(unittest.TestCase):
    def setUp(self) -> None:
        _get_redis_client.cache_clear()
        self.addCleanup(_get_redis_client.cache_clear)

    def test_local_mode_uses_redis_url(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "REDIS_MODE": "url",
                    "REDIS_URL": "redis://localhost:6379/0",
                },
            ),
            patch(
                "redis_store.redis.Redis.from_url",
                return_value=sentinel.redis_client,
            ) as from_url,
        ):
            self.assertIs(_get_redis_client(), sentinel.redis_client)

        from_url.assert_called_once_with(
            "redis://localhost:6379/0",
            decode_responses=True,
        )

    def test_elasticache_mode_uses_iam_credentials_and_tls(self) -> None:
        environment = {
            "REDIS_MODE": "elasticache",
            "ELASTICACHE_HOST": "cache.example",
            "ELASTICACHE_PORT": "6380",
            "ELASTICACHE_USERNAME": "crypto-trader",
            "ELASTICACHE_RESOURCE_ID": "cache-id",
            "ELASTICACHE_CLUSTER_MODE": "false",
            "AWS_REGION": "eu-north-1",
        }
        with (
            patch.dict(os.environ, environment),
            patch(
                "redis_store.ElastiCacheIAMCredentialProvider",
                return_value=sentinel.credentials,
            ) as credentials_provider,
            patch(
                "redis_store.redis.Redis",
                return_value=sentinel.redis_client,
            ) as redis_client,
        ):
            self.assertIs(_get_redis_client(), sentinel.redis_client)

        credentials_provider.assert_called_once_with(
            username="crypto-trader",
            resource_id="cache-id",
            region="eu-north-1",
        )
        redis_client.assert_called_once_with(
            host="cache.example",
            port=6380,
            credential_provider=sentinel.credentials,
            ssl=True,
            decode_responses=True,
        )

    def test_cluster_mode_uses_redis_cluster_client(self) -> None:
        environment = {
            "REDIS_MODE": "elasticache",
            "ELASTICACHE_HOST": "cluster.example",
            "ELASTICACHE_USERNAME": "crypto-trader",
            "ELASTICACHE_RESOURCE_ID": "cluster-id",
            "ELASTICACHE_CLUSTER_MODE": "true",
            "AWS_REGION": "eu-north-1",
        }
        with (
            patch.dict(os.environ, environment),
            patch(
                "redis_store.ElastiCacheIAMCredentialProvider",
                return_value=sentinel.credentials,
            ),
            patch(
                "redis_store.redis.RedisCluster",
                return_value=sentinel.redis_client,
            ) as redis_cluster,
        ):
            self.assertIs(_get_redis_client(), sentinel.redis_client)

        redis_cluster.assert_called_once_with(
            host="cluster.example",
            port=6379,
            credential_provider=sentinel.credentials,
            ssl=True,
            decode_responses=True,
        )

    def test_iam_provider_returns_a_signed_token_as_password(self) -> None:
        session = Mock()
        session.get_credentials.return_value = sentinel.aws_credentials
        signer = Mock()
        signer.generate_presigned_url.return_value = (
            "https://cache-id/?Action=connect&X-Amz-Signature=signed"
        )
        with (
            patch("redis_store.botocore.session.get_session", return_value=session),
            patch("redis_store.RequestSigner", return_value=signer),
        ):
            provider = ElastiCacheIAMCredentialProvider(
                username="crypto-trader",
                resource_id="cache-id",
                region="eu-north-1",
            )

        self.assertEqual(
            provider.get_credentials(),
            ("crypto-trader", "cache-id/?Action=connect&X-Amz-Signature=signed"),
        )
        self.assertEqual(
            signer.generate_presigned_url.call_args.kwargs["expires_in"],
            900,
        )


if __name__ == "__main__":
    unittest.main()
