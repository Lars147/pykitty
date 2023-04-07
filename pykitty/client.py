from datetime import datetime
from typing import Dict, List, Union
from urllib.parse import urlparse

import requests

from pykitty import kitty_parser


def parse_kitty_id(kitty_url) -> str:
    kitty_url_parser = urlparse(kitty_url)

    if "kittysplit." not in kitty_url_parser.netloc:
        raise ValueError("Invalid Domain! Must be a kittysplit domain.")

    kitty_url_parts = kitty_url_parser.path.split(
        "/"
    )  # e.g. ['', 'test_kitty', 'QRMCYapVh-2', 'entries']
    if len(kitty_url_parts) < 3:
        raise ValueError("Invalid URL! Must be a Kittysplit URL.")

    return f"{kitty_url_parts[1]}/{kitty_url_parts[2]}"


def get_csrf_token(
    session: requests.Session, base_url: str, path: str
) -> Union[str, None]:
    response = session.get(base_url + path)
    csrf_parser = kitty_parser.CSRFHTMLParser()
    csrf_parser.feed(response.text)
    return csrf_parser.csrf_token


def kitty_endpoint(
    path,
    method: str = "GET",
    csrf_protected: bool = False,
    user_needs_to_be_selected: bool = False,
):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if user_needs_to_be_selected and self.selected_viewing_party_id is None:
                raise ValueError("No user selected!")

            kwargs.update(
                {
                    "path": path,
                    "method": method,
                }
            )
            if csrf_protected:
                kwargs.update(
                    {
                        "csrf_token": get_csrf_token(self.session, self.base_url, path),
                    }
                )

            # call the function with the modified kwargs
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class KittySplitAPI:
    base_url = "https://kittysplit.de/"

    def __init__(self, kitty_url: str) -> None:
        self.kitty_id = parse_kitty_id(kitty_url)
        self.session: requests.Session = requests.Session()
        self.available_users: Dict[str, str] = self.get_users()
        self.selected_viewing_party_id: Union[str, None] = None

    def _request(
        self,
        method: str,
        path: str,
        data: Union[dict, None] = None,
        csrf_token: Union[str, None] = None,
    ) -> requests.Response:
        url = self.base_url + self.kitty_id + path
        if csrf_token:
            data["_csrf_token"] = csrf_token
        response = self.session.request(method, url, data=data)
        response.raise_for_status()
        return response

    @kitty_endpoint("/entries/")
    def get_users(self, **kwargs) -> Dict[str, str]:
        response = self._request(kwargs.pop("method"), kwargs.pop("path"))
        user_parser = kitty_parser.KittySplitUserParser()
        user_parser.feed(response.text)
        return {name: id for id, name in user_parser.usernames}

    @kitty_endpoint("/parties/set/", method="POST", csrf_protected=True)
    def select_user(self, username: str, **kwargs) -> None:
        # set selected_viewing_party_id
        self.selected_viewing_party_id = self.available_users.get(username)
        if self.selected_viewing_party_id is None:
            raise ValueError(f"{username} not available!")

        form_data = {
            "viewing_party_id": self.selected_viewing_party_id,
        }

        # Select party
        self._request(
            kwargs.pop("method"),
            kwargs.pop("path"),
            csrf_token=kwargs.pop("csrf_token"),
            data=form_data,
        )

    @kitty_endpoint("/entries/", user_needs_to_be_selected=True)
    def get_expenses(self, **kwargs) -> List[dict]:
        response = self._request(kwargs.pop("method"), kwargs.pop("path"))
        return kitty_parser.parse_expenses(response.text)

    @kitty_endpoint(
        "/entries/new/expense/",
        method="POST",
        csrf_protected=True,
        user_needs_to_be_selected=True,
    )
    def add_expense(
        self,
        amount: str,
        description: str,
        entry_date: Union[str, None] = None,
        weight_mapping: Union[Dict[str, float], None] = None,
        **kwargs,
    ) -> None:
        if entry_date is None:
            entry_date = datetime.now().strftime("%Y-%m-%d")

        if weight_mapping is None:
            equal_weight = 1 / len(self.available_users)
            weight_mapping = {
                username: equal_weight for username in self.available_users.keys()
            }

        # Set up the form data
        form_data = {
            "_dontcare": "true",
            "back_to": "",
            "entry[amount]": amount,
            "entry[description]": description,
            "entry[entry_date_str]": entry_date,
            "entry[entry_type]": "expense",
            "entry[party_id]": self.selected_viewing_party_id,
            "entry[split_all_mode]": "none",
            "entry[split_mode]": "weight",
            "select_all": "on",
        }

        idx = 0
        for username, viewing_party_id in self.available_users.items():
            weight = weight_mapping[username]

            form_data[f"entry[entry_shares][{idx}][involved?]"] = "false"
            form_data[f"entry[entry_shares][{idx}][involved?]"] = "true"
            form_data[f"entry[entry_shares][{idx}][number_of_people]"] = ""
            form_data[f"entry[entry_shares][{idx}][number_of_people]"] = "1.0"
            form_data[
                f"entry[entry_shares][{idx}][number_of_people_string]"
            ] = "1 person"
            form_data[f"entry[entry_shares][{idx}][party_id]"] = viewing_party_id
            form_data[f"entry[entry_shares][{idx}][share_display]"] = ""
            form_data[f"entry[entry_shares][{idx}][share_str]"] = str(
                round(float(amount) * weight, 3)
            )
            form_data[f"entry[entry_shares][{idx}][weight]"] = str(weight)

            idx += 1

        self._request(
            kwargs.pop("method"),
            kwargs.pop("path"),
            csrf_token=kwargs.pop("csrf_token"),
            data=form_data,
        )
