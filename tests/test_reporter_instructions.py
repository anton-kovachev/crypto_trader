import json
import unittest

from instructions import reporter_instructions


class ReporterInstructionsTests(unittest.TestCase):
    def test_snapshot_template_is_valid_json_and_account_specific(self) -> None:
        prompt = reporter_instructions("Max Kaiser")
        serialized_template = prompt.split("```json", 1)[1].split("```", 1)[0]
        snapshot_template = json.loads(serialized_template)

        self.assertIn("Max Kaiser", prompt)
        self.assertIn("total_holding_values_time_series", prompt)
        self.assertIn("usdc_value", snapshot_template["metadata"]["assets"][0])
        self.assertEqual(
            snapshot_template["metadata"]["totals"],
            {"usd": 0.0, "usdc": 0.0, "btc": 0.0},
        )


if __name__ == "__main__":
    unittest.main()
