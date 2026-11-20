import unittest
from unittest.mock import MagicMock, call, patch

import requests

from pykitty.client import KittySplitAPI


class TestKittySplitAPI(unittest.TestCase):
    def setUp(self):
        self.kitty_url = "https://kittysplit.de/test_kitty/ADLKFJLAKD/"
        self.username = "test-user"

    @patch.object(KittySplitAPI, "get_users")
    def test_init(self, mock_get_users):
        mock_get_users.return_value = {"test-user1": "1", "test-user2": "2"}
        api = KittySplitAPI(self.kitty_url)
        self.assertEqual(api.kitty_id, "test_kitty/ADLKFJLAKD")
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
        api = KittySplitAPI(self.kitty_url)
        users = api.get_users()
        self.assertEqual(users, expected_users)
        mock_get.assert_called_with(
            "GET", api.base_url + api.kitty_id + "/entries/", data=None
        )

    @patch.object(requests.Session, "request")
    def test_select_legacy_user(self, request):
        chooser = MagicMock(
            text="""
            <form class="set-viewing-party">
                <input name="viewing_party_id" value="1">
                <button>Example One</button>
            </form>
        """
        )
        token_page = MagicMock(text='<input name="_csrf_token" value="example-token">')
        request.side_effect = [chooser, token_page, MagicMock()]

        api = KittySplitAPI(self.kitty_url)
        api.select_user("Example One")

        request.assert_called_with(
            "POST",
            f"{api.base_url}{api.kitty_id}/parties/set/",
            data={"viewing_party_id": "1", "_csrf_token": "example-token"},
        )
        self.assertEqual(api.selected_viewing_party_id, "1")


class TestParticipantChooser(unittest.TestCase):
    kitty_url = "https://www.kittysplit.com/k/example-chooser"
    chooser_url = f"{kitty_url}/parties/choose"
    action_url = f"{kitty_url}/parties/example-one/set"
    chooser_html = """
        <form method="post" action="/k/example-chooser/parties/choose">
            <input type="hidden" name="_csrf_token" value="example-chooser-token">
            <button type="submit" formaction="/k/example-chooser/parties/example-one/set">
                Example One
            </button>
            <button type="submit" formaction="/k/example-chooser/parties/example-two/set">
                Example Two
            </button>
            <button type="submit" formaction="https://example.invalid/parties/foreign/set">
                Foreign Action
            </button>
        </form>
    """

    @patch.object(requests.Session, "request")
    def test_select_participant_and_continue_without_account(self, request):
        chooser = MagicMock(text=self.chooser_html)
        confirmation = MagicMock(
            text="""
            <form method="post" action="/k/example-chooser/parties/example-one/set">
                <input type="hidden" name="_csrf_token" value="example-guest-token">
                <input type="hidden" name="skip_account_prompt" value="true">
                <button type="submit">Continue without account</button>
            </form>
        """
        )
        request.side_effect = [
            chooser,
            chooser,
            confirmation,
            MagicMock(text="", url=self.kitty_url),
        ]

        api = KittySplitAPI(self.kitty_url)
        self.assertEqual(
            api.available_users,
            {"Example One": "example-one", "Example Two": "example-two"},
        )
        api.select_user("Example One")

        self.assertEqual(api.selected_viewing_party_id, "example-one")
        self.assertEqual(
            request.call_args_list,
            [
                call("GET", self.chooser_url, data=None),
                call("GET", self.chooser_url, data=None),
                call(
                    "POST",
                    self.action_url,
                    data={"_csrf_token": "example-chooser-token"},
                ),
                call(
                    "POST",
                    self.action_url,
                    data={
                        "skip_account_prompt": "true",
                        "_csrf_token": "example-guest-token",
                    },
                ),
            ],
        )

    @patch.object(requests.Session, "request")
    def test_missing_token_never_posts_selection(self, request):
        request.return_value = MagicMock(
            text=self.chooser_html.replace('value="example-chooser-token"', "")
        )
        api = KittySplitAPI(self.kitty_url)

        with self.assertRaisesRegex(ValueError, "missing a CSRF token"):
            api.select_user("Example One")

        self.assertIsNone(api.selected_viewing_party_id)
        self.assertEqual(
            request.call_args_list, [call("GET", self.chooser_url, data=None)] * 2
        )

    @patch.object(requests.Session, "request")
    def test_missing_guest_option_does_not_confirm_selection(self, request):
        chooser = MagicMock(text=self.chooser_html)
        prompt = MagicMock(
            text="", url=f"{self.kitty_url}/parties/example-one/account-prompt"
        )
        request.side_effect = [chooser, chooser, prompt]
        api = KittySplitAPI(self.kitty_url)

        with self.assertRaisesRegex(ValueError, "did not confirm"):
            api.select_user("Example One")

        self.assertIsNone(api.selected_viewing_party_id)
        self.assertEqual(request.call_count, 3)
