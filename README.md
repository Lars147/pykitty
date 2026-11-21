<!-- Codecov Coverage Badge -->
[![codecov](https://codecov.io/gh/Lars147/pykitty/graph/badge.svg?token=TOY40XZ1QU)](https://codecov.io/gh/Lars147/pykitty)

<!-- Sonar Cloud Quality Badge -->
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Lars147_pykitty&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Lars147_pykitty)

# PyKitty

This Python SDK allows you to interact with [KittySplit](https://kittysplit.de/) to manage expenses in a group. You can fetch a list of users, select a user and add expenses.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
    - [Get Users](#get-users)
    - [Select User](#select-user)
    - [Add Expense](#add-expense)
    - [Get Expenses](#get-expenses)
    - [Get Single Expense Details](#get-single-expense-details)
    - [Delete Expense](#delete-expense)
- [Releasing](#releasing)
- [License](#license)
- [Next Steps (TODO)](#next-steps-todo)

## Installation

PyKitty requires Python 3.9 or newer. To install the package, run:

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
api.get_users()  # {"user1": "3451816", "user2": "7167080"}
```

This will return a dictionary with usernames as keys and user IDs as values.

### Select User

You have to select an user of the KittySplit. Use the `select_user` method to set your user:

```python
api.select_user("<your_username>")
```

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
api.get_expenses()  # list all expenses
```
```python
api.get_expenses("yours")  # list expenses you paid
```
```python
api.get_expenses("others")  # list expenses others have paid
```
### Get Single Expense Details
```python
api.get_expense("8233711")  # expense_id can be found in URL
```


### Delete Expense
```python
api.delete_expense("8233711")  # expense_id can be found in URL
```

## Releasing

`pyproject.toml` holds the package version. Use `poetry version patch`,
`poetry version minor`, or `poetry version major` to bump it in a pull request.

Before the first release, create the `pypi` environment under **Settings →
Environments** in GitHub and allow deployments from tags matching `v*`. In
[PyPI project settings](https://pypi.org/manage/project/pykitty/settings/publishing/),
add a GitHub Trusted Publisher with these values.

| Field | Value |
| --- | --- |
| Owner | `Lars147` |
| Repository | `pykitty` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

After merging the version bump and checking CI, tag the commit on `main` with
the matching `vMAJOR.MINOR.PATCH` tag. For the first automated release, use the
commit with version `0.4.0`.

```bash
git switch main
git pull --ff-only
git tag -a v0.4.0 -m "Release 0.4.0"
git push origin v0.4.0
```

GitHub Actions checks the tag, tests the package, builds a wheel and source
distribution, and uploads both via PyPI Trusted Publishing. It then creates a
GitHub Release with generated notes. If the PyPI upload succeeds and the
GitHub Release step fails, rerun the failed job from the same workflow run.

## License

This project is licensed under the MIT License.

## Next Steps (TODO)

- [x] Parse Kitty URL to extract `kitty_id`
- [x] Implement `get_expenses` method to retrieve all expenses.
- [x] Add support for deleting expenses.
- [x] Enhance test coverage.
- [ ] Add support for updating expenses.
- [ ] Document CLI usage.
- [ ] Support for Kittysplit in other languages.
