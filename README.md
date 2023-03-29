# PyKitty

This Python SDK allows you to interact with [KittySplit](www.kittysplit.de/) to manage expenses in a group. You can fetch a list of users, select a user and add expenses.

## Installation

To install the package, use the following command:

```bash
pip install pykitty
```

## Usage

1. Open a kitty on https://kittysplit.de/
2. Once opened, you can extract your `kitty_id` from the URL, e.g. `test_kitty/ADLKFJLAKD.../` in https://kittysplit.de/test_kitty/ADLKFJLAKD.../

Create an instance of the `KittySplitAPI` class with the Kitty ID:

```python
from pykitty import KittySplitAPI
api = KittySplitAPI("your_kitty_id")
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
    entry_date="2023-03-29",
    weight_mapping={"username1": 0.6, "username2": 0.4},  # optional, if not specified, expense will be split evenly
)
```

This method will add a new expense with the specified details.

## License

This project is licensed under the MIT License.

## Next Steps (TODO)

- [ ] Add Kitty URL parser to extract `kitty_id` and language from any kittysplit URL
- [ ] Implement `get_expenses` method to retrieve all expenses.
- [ ] Add support for updating and deleting expenses.
- [ ] Document CLI usage.
