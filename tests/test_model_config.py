import os
import unittest
from unittest.mock import patch

from model_config import DEFAULT_MODEL_NAME, resolve_model_name


class ModelConfigTests(unittest.TestCase):
    def test_missing_or_empty_environment_uses_default(self) -> None:
        for value in (None, "", "   ", "None"):
            with self.subTest(value=value), patch.dict(os.environ, {}, clear=True):
                if value is not None:
                    os.environ["MODEL_NAME"] = value
                self.assertEqual(resolve_model_name(), DEFAULT_MODEL_NAME)

    def test_environment_value_is_used(self) -> None:
        with patch.dict(os.environ, {"MODEL_NAME": "custom-model"}, clear=True):
            self.assertEqual(resolve_model_name(), "custom-model")

    def test_explicit_value_overrides_environment(self) -> None:
        with patch.dict(os.environ, {"MODEL_NAME": "environment-model"}, clear=True):
            self.assertEqual(resolve_model_name("explicit-model"), "explicit-model")

    def test_blank_explicit_value_falls_back_to_environment(self) -> None:
        with patch.dict(os.environ, {"MODEL_NAME": "environment-model"}, clear=True):
            self.assertEqual(resolve_model_name("  "), "environment-model")


if __name__ == "__main__":
    unittest.main()
