import csv
import time
from datetime import datetime
from typing import Union

import typer
from rich.progress import track

from pykitty import client

app = typer.Typer()


def convert_date_format(date_string: str) -> str:
    datetime_obj = datetime.strptime(date_string, "%d.%m.%Y")
    return datetime_obj.strftime("%Y-%m-%d")


@app.callback()
def callback():
    """
    Awesome Kitty CLI
    """


@app.command()
def add_expenses(
    kitty_url: str,
    kitty_username: str,
    csv_file: typer.FileText,
    expense_weight: Union[float, None] = None,
    timeout_between_requests: float = 0.5,
):
    """Adds expenses to Kittysplit

    Args:
        kitty_url (str): The Kittysplit url, e.g. https://kittysplit.de/test_kitty/ADFKYapVh5_N4wlMKZmPFhAiGqfz2_44-2
        kitty_username (str): Your Kittysplit username.
        csv_file (typer.FileText): The path to the csv file, e.g. "~/expenses.csv"
        expense_weight (float, optional): The weights for your expenses, e.g. '0.4' would assign your expenses a weight of 0.4 while it distributes the weights of the other users equally. Defaults to None.
        timeout_between_requests (float, optional): Be nice to Kittysplit and add timeouts between the requests. Defaults to 0.5.
    """
    kitty_api = client.KittySplitAPI(kitty_url)
    kitty_api.select_user(kitty_username)

    # calculate weight mapping
    if expense_weight is not None:
        weight_mapping = dict()
        for username in kitty_api.available_users.keys():
            if username == kitty_username:
                weight_mapping[kitty_username] = expense_weight
            else:
                weight_mapping[username] = (1 - expense_weight) / len(
                    kitty_api.available_users.keys()
                )
    else:
        weight_mapping = None

    # read csv file
    reader = csv.DictReader(csv_file, delimiter=";")
    expenses = list()
    for row in reader:
        expenses.append(
            {
                "amount": str(-float(row["Betrag"].replace(",", "."))),
                "description": row["Name"],
                "entry_date": convert_date_format(row["Datum"]),
            }
        )

    # add expenses to Kittysplit
    added_expenses_counter = 0
    for expense in track(expenses, description="Adding expenses..."):
        kitty_api.add_expense(
            amount=expense["amount"],
            description=expense["description"],
            entry_date=expense["entry_date"],
            weight_mapping=weight_mapping,
        )
        added_expenses_counter += 1

        time.sleep(timeout_between_requests)

    print(
        f"Added {added_expenses_counter} expenses! Total expenses amount added: {sum([float(expense['amount']) for expense in expenses])}"
    )
    print()
    print("Check your expenses! Will open your kitty...")
    typer.launch(f"https://kittysplit.de/{kitty_api.kitty_id}/entries/")


if __name__ == "__main__":
    app()
