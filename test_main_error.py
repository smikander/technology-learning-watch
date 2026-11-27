import unittest
from unittest.mock import patch
import requests

from main import main


class TestMainError(unittest.TestCase):

    @patch("main.save_history")
    @patch("main.generate_report")
    @patch("main.analyze_article")
    @patch("main.fetch_articles")
    @patch("main.load_history")
    def test_analysis_failure(
        self,
        mock_history,
        mock_fetch,
        mock_analyze,
        mock_report,
        mock_save
    ):
        mock_history.return_value = set()

        mock_fetch.return_value = (
            [
                {
                    "title": "Testiartikkeli",
                    "description": "Virheenkäsittelyn testi.",
                    "url": "https://example.com/test"
                }
            ],
            []
        )

        mock_analyze.side_effect = requests.ConnectionError(
            "Simuloitu yhteysvirhe"
        )

        result = main()

        self.assertEqual(result, 1)
        mock_analyze.assert_called_once()
        mock_report.assert_not_called()
        mock_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
    