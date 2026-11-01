import os
import unittest
from unittest.mock import patch

from crypto_agents.openrouter_client import (
    OPENROUTER_BASE_URL,
    create_openrouter_client,
)


class OpenRouterClientTests(unittest.TestCase):
    def test_uses_configured_api_key_and_base_url(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "test-key",
                    "OPENROUTER_BASE_URL": "https://openrouter.example/api/v1",
                },
                clear=True,
            ),
            patch("crypto_agents.openrouter_client.AsyncOpenAI") as client_factory,
        ):
            client = create_openrouter_client()

        self.assertIs(client, client_factory.return_value)
        client_factory.assert_called_once_with(
            api_key="test-key",
            base_url="https://openrouter.example/api/v1",
        )

    def test_defaults_empty_base_url_and_rejects_missing_api_key(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"OPENROUTER_API_KEY": "test-key", "OPENROUTER_BASE_URL": "  "},
                clear=True,
            ),
            patch("crypto_agents.openrouter_client.AsyncOpenAI") as client_factory,
        ):
            create_openrouter_client()

        client_factory.assert_called_once_with(
            api_key="test-key",
            base_url=OPENROUTER_BASE_URL,
        )

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY"):
                create_openrouter_client()


if __name__ == "__main__":
    unittest.main()
