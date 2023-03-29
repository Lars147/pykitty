import unittest

from pykitty.kitty_parser import CSRFHTMLParser, KittySplitUserParser


class TestCSRFHTMLParser(unittest.TestCase):
    def setUp(self):
        self.parser = CSRFHTMLParser()

    def test_handle_starttag_should_set_csrf_token_if_input_tag_with_correct_name_and_value(
        self,
    ):
        tag = "input"
        attrs = [("name", "_csrf_token"), ("value", "token123")]

        self.parser.handle_starttag(tag, attrs)

        self.assertEqual(self.parser.csrf_token, "token123")

    def test_handle_starttag_should_not_set_csrf_token_if_input_tag_with_different_name_or_value(
        self,
    ):
        tag = "input"
        attrs = [("name", "_different_name"), ("value", "token123")]

        self.parser.handle_starttag(tag, attrs)

        self.assertIsNone(self.parser.csrf_token)

    def test_handle_starttag_should_not_set_csrf_token_if_tag_is_not_input(self):
        tag = "button"
        attrs = [("name", "_csrf_token"), ("value", "token123")]

        self.parser.handle_starttag(tag, attrs)

        self.assertIsNone(self.parser.csrf_token)


class TestKittySplitUserParser(unittest.TestCase):
    def test_handle_starttag_with_form(self):
        parser = KittySplitUserParser()
        parser.handle_starttag("form", [("class", "set-viewing-party")])
        self.assertTrue(parser.in_form)

    def test_handle_starttag_with_input(self):
        parser = KittySplitUserParser()
        parser.in_form = True
        parser.handle_starttag(
            "input", [("name", "viewing_party_id"), ("value", "1234")]
        )
        self.assertEqual(parser.party_ids, ["1234"])

    def test_handle_starttag_with_button(self):
        parser = KittySplitUserParser()
        parser.in_form = True
        parser.party_ids = ["1234", "5678"]
        parser.handle_starttag("button", [])
        self.assertEqual(parser.viewing_party_id, "5678")

    def test_parse(self):
        html = """
            <html>
                <form class="set-viewing-party">
                    <input name="viewing_party_id" value="1234">
                    <button>Party 1</button>
                </form>
                <form class="set-viewing-party">
                    <input name="viewing_party_id" value="5678">
                    <button>Party 2</button>
                </form>
            </html>
        """
        parser = KittySplitUserParser()
        parser.feed(html)
        self.assertEqual(parser.party_ids, ["1234", "5678"])
        self.assertEqual(parser.usernames, [("1234", "Party 1"), ("5678", "Party 2")])
