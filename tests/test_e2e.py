import os
import unittest
from datetime import datetime

from pykitty.client import KittySplitAPI


class TestKittySplitAPIE2E(unittest.TestCase):
    def setUp(self):
        self.kitty_url = os.environ["E2E_KITTY_URL"]
        self.username = os.environ["E2E_KITTY_USERNAME"]
        self.test_expense_description = "test-expense-id"

    def test_get_user(self):
        api = KittySplitAPI(self.kitty_url)
        self.assertIn(self.username, api.get_users())

    def test_set_user(self):
        api = KittySplitAPI(self.kitty_url)
        users = api.get_users()

        selected_user_viewing_party_id = users[self.username]
        api.select_user(self.username)

        self.assertEqual(api.selected_viewing_party_id, selected_user_viewing_party_id)

    def test_crud_expense(self):
        api = KittySplitAPI(self.kitty_url)
        api.select_user(self.username)

        api.add_expense(
            amount="10.00",
            description=self.test_expense_description,
            entry_date="2024-03-28",
        )

        # find the expense we just added in the list of expenses
        expenses = api.get_expenses()
        expense_created = [
            expense
            for expense in expenses
            if expense["description"] == self.test_expense_description
        ][0]

        self.assertEqual(expense_created["buyer"], self.username)
        self.assertEqual(expense_created["price"]["amount"], "10.00")
        self.assertEqual(expense_created["share"], "5.00")
        self.assertEqual(expense_created["participants"], "all")
        self.assertEqual(expense_created["date"], datetime(2024, 3, 28))

        # get the detailed expense
        detailed_expense = api.get_expense(expense_created["id"])

        self.assertEqual(detailed_expense["entry_type"], "expense")
        self.assertEqual(detailed_expense["description"], self.test_expense_description)
        self.assertEqual(detailed_expense["party_id"], api.selected_viewing_party_id)

        # delete the expense
        api.delete_expense(expense_created["id"])

        # make sure the expense was deleted
        expenses = api.get_expenses()
        expense_created = [
            expense
            for expense in expenses
            if expense["description"] == self.test_expense_description
        ]
        self.assertEqual(len(expense_created), 0)
