import unittest
from unittest.mock import MagicMock, patch

import requests

from pykitty.client import KittySplitAPI


class TestKittySplitAPI(unittest.TestCase):
    def setUp(self):
        self.kitty_id = "test-kitty-id"
        self.username = "test-user"

    @patch.object(KittySplitAPI, "get_users")
    def test_init(self, mock_get_users):
        mock_get_users.return_value = {"test-user1": "1", "test-user2": "2"}
        api = KittySplitAPI(self.kitty_id)
        self.assertEqual(api.kitty_id, self.kitty_id)
        self.assertEqual(api.available_users, {"test-user1": "1", "test-user2": "2"})
        self.assertIsNone(api.selected_viewing_party_id)

    @patch.object(requests.Session, "request")
    def test_get_users(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = """
            <html>
                <form class="set-viewing-party">
                    <input name="viewing_party_id" value="1">
                    <button>test-user1</button>
                </form>
                <form class="set-viewing-party">
                    <input name="viewing_party_id" value="2">
                    <button>test-user2</button>
                </form>
            </html>
        """
        mock_get.return_value = mock_response
        expected_users = {"test-user1": "1", "test-user2": "2"}
        mock_parser = MagicMock()
        mock_parser.usernames = [(id, name) for name, id in expected_users.items()]
        api = KittySplitAPI(self.kitty_id)
        users = api.get_users()
        self.assertEqual(users, expected_users)
        mock_get.assert_called_with(
            "GET", api.base_url + self.kitty_id + "/entries/", data=None
        )
