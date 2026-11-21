import unittest
from datetime import datetime

from pykitty.kitty_parser import (
    CSRFHTMLParser,
    ExpenseType,
    KittySplitUserParser,
    parse_expenses,
)


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
    def test_current_expense_summary_and_participant_filters(self):
        html = """
            <li class="entry-list-item entry-all" data-paid-by-id="payer"
                data-share-party-ids="payer,guest">
                <a class="entry-link" href="/k/example-chooser/entries/example-expense">
                    <div class="entry-main">Example One paid €10.00 for Example lunch</div>
                    <span class="entry-label entry-label-date">03/28/2024</span>
                    <span class="entry-label entry-label-share accent-color-primary">
                        Your share: €5.00
                    </span>
                    <span class="entry-label entry-label-parties">
                        People involved: <span>everyone</span>.
                    </span>
                </a>
            </li>
        """
        expected = [
            {
                "url": "/k/example-chooser/entries/example-expense",
                "id": "example-expense",
                "buyer": "Example One",
                "price": {"currency": "€", "amount": "10.00"},
                "description": "Example lunch",
                "date": datetime(2024, 3, 28),
                "share": "5.00",
                "participants": "all",
            }
        ]
        self.assertEqual(parse_expenses(html, ExpenseType.ALL), expected)
        self.assertEqual(parse_expenses(html, ExpenseType.YOURS, "guest"), expected)
        self.assertEqual(parse_expenses(html, ExpenseType.OTHERS, "guest"), [])
        self.assertEqual(parse_expenses(html, ExpenseType.OTHERS, "other"), expected)

    def test_legacy_filter_preserves_named_participants(self):
        html = """
            <li class="py-1 entry-list-item entry-all entry-others">
                <a class="entry-link" href="/test_kitty/example-chooser/entries/example-expense/edit">
                    <div class="col-xs-11">Example One paid €10.00 for Example lunch</div>
                    <span class="entry-label entry-label-date">03/28/2024</span>
                    <span class="entry-label entry-label-parties">
                        People involved: <span>Example One, Example Two</span>.
                    </span>
                </a>
            </li>
        """

        entries = parse_expenses(html, ExpenseType.OTHERS, "example-viewer")

        self.assertEqual(
            [entry["participants"] for entry in entries], ["Example One, Example Two"]
        )
        self.assertEqual(parse_expenses(html, ExpenseType.YOURS, "example-viewer"), [])

    def test_invalid_expense_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid expense type: unknown"):
            parse_expenses("", "unknown")

    def test_parse_expenses(self):
        german_html = """
        <html>

        <ul class="entries list-unstyled">
            <li class="py-1 entry-list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233980/edit">
                    <div class="row">
                        <div class="col-xs-11">
                            Test User hat <span class="currency"><span class="currency-symbol">€</span>23,57</span> für EDEKA Muenchen DE bezahlt.
                        </div>
                        <div class="col-xs-1">
                            <div class="edit-entry">
                                <i class="fa-icon fas fa-edit text-muted"></i>
                            </div>
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
            <li class="py-1 entry-list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233979/edit">
                    <div class="row">
                        <div class="col-xs-11">
                            Test User hat <span class="currency"><span class="currency-symbol">€</span>0,85</span> für Backstube Muenchen DE bezahlt.
                        </div>
                        <div class="col-xs-1">
                            <div class="edit-entry">
                                <i class="fa-icon fas fa-edit text-muted"></i>
                            </div>
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
            <li class="py-1 entry-list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233980/edit">
                    <div class="row">
                        <div class="col-xs-11">
                            Test User paid <span class="currency"><span class="currency-symbol">€</span>23.57</span> for EDEKA Muenchen DE
                        </div>
                        <div class="col-xs-1">
                            <div class="edit-entry">
                                <i class="fa-icon fas fa-edit text-muted"></i>
                            </div>
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
            <li class="py-1 entry-list-item entry-all entry-yours">
                <a class="entry-link" href="/test_kitty/ADLKFJLAKD/entries/8233979/edit">
                    <div class="row">
                        <div class="col-xs-11">
                            Test User paid <span class="currency"><span class="currency-symbol">€</span>0.85</span> for Backstube Muenchen DE
                        </div>
                        <div class="col-xs-1">
                            <div class="edit-entry">
                                <i class="fa-icon fas fa-edit text-muted"></i>
                            </div>
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

        expected_output_german = [
            {
                "url": "/test_kitty/ADLKFJLAKD/entries/8233980/edit",
                "id": "8233980",
                "buyer": "Test User",
                "price": {"currency": "€", "amount": "23.57"},
                "description": "EDEKA Muenchen DE",
                "date": datetime(2023, 3, 27),
                "share": "11.79",
                "participants": "all",
            },
            {
                "url": "/test_kitty/ADLKFJLAKD/entries/8233979/edit",
                "id": "8233979",
                "buyer": "Test User",
                "price": {"currency": "€", "amount": "0.85"},
                "date": datetime(2023, 3, 27),
                "share": "0.43",
                "description": "Backstube Muenchen DE",
                "participants": "all",
            },
        ]
        expected_output_english = [
            {
                "url": "/test_kitty/ADLKFJLAKD/entries/8233980/edit",
                "id": "8233980",
                "buyer": "Test User",
                "price": {"currency": "€", "amount": "23.57"},
                "description": "EDEKA Muenchen DE",
                "date": datetime(2023, 3, 6),
                "share": "4.47",
                "participants": "all",
            },
            {
                "url": "/test_kitty/ADLKFJLAKD/entries/8233979/edit",
                "id": "8233979",
                "buyer": "Test User",
                "price": {"currency": "€", "amount": "0.85"},
                "date": datetime(2023, 3, 6),
                "share": "13.10",
                "description": "Backstube Muenchen DE",
                "participants": "all",
            },
        ]

        self.assertEqual(
            parse_expenses(german_html, expense_type=ExpenseType.ALL),
            expected_output_german,
        )
        self.assertEqual(
            parse_expenses(english_html, expense_type=ExpenseType.ALL),
            expected_output_english,
        )
