import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import requests

from services.coinmarketcap_base_service import get_cryptocurrency_data


class CoinMarketCapBaseServiceTests(unittest.TestCase):
    def test_request_errors_are_raised_without_writing_to_stdout(self) -> None:
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("request failed")
        stdout = io.StringIO()

        with patch(
            "services.coinmarketcap_base_service.requests.get",
            return_value=response,
        ):
            with redirect_stdout(stdout), self.assertRaises(requests.HTTPError):
                get_cryptocurrency_data("/listings/latest")

        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
