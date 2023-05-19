# PyKitty

This Python SDK allows you to interact with [KittySplit](https://kittysplit.de/) to manage expenses in a group. You can fetch a list of users, select a user and add expenses.

## Installation

To install the package, use the following command:

```bash
pip install pykitty
```

## Usage

1. Open a kitty on https://kittysplit.de/ and set a username
2. Once opened, copy the full Kittysplit URL, e.g. `https://kittysplit.de/test_kitty/ADLKFJLAKD.../`

Create your first expense with the following code (replace `<kitty_URL>` and `<your_username>`):

```python
from pykitty import KittySplitAPI
api = KittySplitAPI("<kitty_URL>")
api.select_user("<your_username>")
api.add_expense(
    amount="10.00",
    description="A warm welcome by pykitty!",
)
```

### Get Users

To fetch a list of users, use the `get_users` method:

```python
users = api.get_users()
```

This will return a dictionary with usernames as keys and user IDs as values.

### Select User

To select a user, use the `select_user` method:

```python
api.select_user("username")
```

This method will set the `selected_viewing_party_id` attribute to the ID of the specified user.

### Add Expense

To add an expense, use the `add_expense` method:

```python
api.add_expense(
    amount="10.00",
    description="Lunch",
)
```

This method will add a new expense with the specified details.

With the `entry_date` parameter, you can specify the date of the expense:

```python
api.add_expense(
    amount="10.00",
    description="Lunch",
    entry_date="2023-03-29",
)
```

With the `weight_mapping` parameter, you can specify how much each user should pay for the expense. The sum of the weights must be `1`.

```python
api.add_expense(
    amount="10.00",
    description="Lunch",
    weight_mapping={"username1": 0.6, "username2": 0.4},
)
```

### Get Expenses
```python
api.get_expenses()
```

## License

This project is licensed under the MIT License.

## Next Steps (TODO)

- [x] Parse Kitty URL to extract `kitty_id` 
- [x] Implement `get_expenses` method to retrieve all expenses.
- [x] Add support for deleting expenses.
- [ ] Enhance test coverage.
- [ ] Add support for updating expenses.
- [ ] Document CLI usage.
- [ ] Support for Kittysplit in other languages.
