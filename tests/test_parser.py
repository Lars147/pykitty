import unittest

from pykitty.kitty_parser import (CSRFHTMLParser, KittySplitUserParser,
                                  parse_expenses)


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


class TestParseExpenses(unittest.TestCase):
    def test_parse_expenses(self):
        german_html = """
        <html>
        <ul class="entries list-unstyled">
            <li class="entry-list-item list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233980/edit">
                    <div class="row">
                        <div class="col-xs-12">
                            Test User hat <span class="currency"><span class="currency-symbol">€</span>23,57</span> für EDEKA Muenchen DE bezahlt.
                        </div>
                    </div>
                    <div class="row">
                        <div class="entry-meta col-xs-12">
                            <span class="entry-label entry-label-parties">
                                Teilnehmer: <span class="entry-parties">Alle</span>.
                            </span>
                            <span class="entry-label entry-label-date">
                                27.03.2023
                            </span>
                            <span class="entry-label entry-label-share accent-color-primary">Dein Anteil: <span class="currency"><span class="currency-symbol">€</span>11,79</span></span>
                        </div>
                    </div>
                </a>
            </li>
            <li class="entry-list-item list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233979/edit">
                    <div class="row">
                        <div class="col-xs-12">
                            Test User hat <span class="currency"><span class="currency-symbol">€</span>0,85</span> für Backstube Muenchen DE bezahlt.
                        </div>
                    </div>
                    <div class="row">
                        <div class="entry-meta col-xs-12">
                            <span class="entry-label entry-label-parties">
                                Teilnehmer: <span class="entry-parties">Alle</span>.
                            </span>
                            <span class="entry-label entry-label-date">
                                27.03.2023
                            </span>
                            <span class="entry-label entry-label-share accent-color-primary">Dein Anteil: <span class="currency"><span class="currency-symbol">€</span>0,43</span></span>
                        </div>
                    </div>
                </a>
            </li>
        </ul>

        </html>
        """

        english_html = """
        <html>
        <ul class="entries list-unstyled">
            <li class="entry-list-item list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233980/edit">
                    <div class="row">
                        <div class="col-xs-12">
                            Test User paid <span class="currency"><span class="currency-symbol">€</span>23.57</span> for EDEKA Muenchen DE
                        </div>
                    </div>
                    <div class="row">
                        <div class="entry-meta col-xs-12">
                            <span class="entry-label entry-label-parties">
                                People involved: <span class="entry-parties">everyone</span>.
                            </span>
                            <span class="entry-label entry-label-date">
                                03/06/2023
                            </span>
                            <span class="entry-label entry-label-share accent-color-primary">Your share: <span class="currency"><span class="currency-symbol">€</span>4.47</span></span>
                        </div>
                    </div>
                </a>
            </li>
            <li class="entry-list-item list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233979/edit">
                    <div class="row">
                        <div class="col-xs-12">
                            Test User paid <span class="currency"><span class="currency-symbol">€</span>0.85</span> for Backstube Muenchen DE
                        </div>
                    </div>
                    <div class="row">
                        <div class="entry-meta col-xs-12">
                            <span class="entry-label entry-label-parties">
                                People involved: <span class="entry-parties">everyone</span>.
                            </span>
                            <span class="entry-label entry-label-date">
                                03/06/2023
                            </span>
                            <span class="entry-label entry-label-share accent-color-primary">Your share: <span class="currency"><span class="currency-symbol">€</span>13.10</span></span>
                        </div>
                    </div>
                </a>
            </li>
        </ul>

        </html>
        """

        expected_output = [
            {
                "url": "/test_kitty/ADLKFJLAKD/entries/8233980/edit",
                "buyer": "Test User",
                "price": {"currency": "€", "amount": "23.57"},
                "description": "EDEKA Muenchen DE",
                "participants": "all",
            },
            {
                "url": "/test_kitty/ADLKFJLAKD/entries/8233979/edit",
                "buyer": "Test User",
                "price": {"currency": "€", "amount": "0.85"},
                "description": "Backstube Muenchen DE",
                "participants": "all",
            },
        ]

        self.assertEqual(parse_expenses(german_html), expected_output)
        self.assertEqual(parse_expenses(english_html), expected_output)
