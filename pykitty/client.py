from datetime import datetime
from typing import Dict, List, Tuple, Union
from urllib.parse import quote, urlparse

import requests

from pykitty import kitty_parser


def fill_query_params(query, *args):
    return query.format(*[quote(arg, safe="") for arg in args])


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

            endpoint = path.rstrip("/") if self._uses_participant_chooser else path
            kwargs.update(
                {
                    "path": endpoint,
                    "method": method,
                }
            )
            if csrf_protected:
                if self._uses_participant_chooser:
                    kwargs["csrf_token"] = self._get_form_token(endpoint, endpoint)
                else:
                    kwargs["csrf_token"] = get_csrf_token(
                        self.session, self.base_url, path
                    )

            # call the function with the modified kwargs
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class KittySplitAPI:
    base_url = "https://kittysplit.de/"

    def __init__(self, kitty_url: str) -> None:
        self.kitty_id = parse_kitty_id(kitty_url)
        self._uses_participant_chooser = self.kitty_id.startswith("k/")
        if self._uses_participant_chooser:
            self.base_url = "https://www.kittysplit.com/"
        self.session: requests.Session = requests.Session()
        self.selected_viewing_party_id: Union[str, None] = None
        self.available_users: Dict[str, str] = self.get_users()

    def _get_form_token(self, page: str, action: str) -> str:
        response = self._request("GET", page)
        token = kitty_parser.parse_form_csrf_token(
            response.text, f"/{self.kitty_id}{action}"
        )
        if not token:
            raise ValueError("Kittysplit form is missing a CSRF token.")
        return token

    def _request(
        self,
        method: str,
        path: str,
        data: Union[dict, None] = None,
        csrf_token: Union[str, None] = None,
    ) -> requests.Response:
        url = self.base_url + self.kitty_id + path
        if csrf_token:
            data = {**(data or {}), "_csrf_token": csrf_token}
        response = self.session.request(method, url, data=data)
        response.raise_for_status()
        return response

    def _get_participant_chooser(self) -> Tuple[Dict[str, str], Union[str, None]]:
        response = self._request("GET", "/parties/choose")
        return kitty_parser.parse_participant_chooser(response.text, self.kitty_id)

    def get_users(self, **kwargs) -> Dict[str, str]:
        if self._uses_participant_chooser:
            users, _ = self._get_participant_chooser()
            return users
        response = self._request("GET", "/entries/")
        user_parser = kitty_parser.KittySplitUserParser()
        user_parser.feed(response.text)
        return {name: id for id, name in user_parser.usernames}

    def select_user(self, username: str, **kwargs) -> None:
        users, token = (
            self._get_participant_chooser()
            if self._uses_participant_chooser
            else (self.available_users, None)
        )

        party_id = users.get(username)
        if party_id is None:
            raise ValueError(f"{username} not available!")

        if self._uses_participant_chooser:
            if not token:
                raise ValueError(
                    "Kittysplit participant chooser is missing a CSRF token."
                )
            self._select_participant(party_id, token)
            self.available_users = users
        else:
            path = "/parties/set/"
            self._request(
                "POST",
                path,
                data={"viewing_party_id": party_id},
                csrf_token=get_csrf_token(self.session, self.base_url, path),
            )
        self.selected_viewing_party_id = party_id

    def _select_participant(self, party_id: str, token: str) -> None:
        path = fill_query_params("/parties/{}/set", party_id)
        response = self._request("POST", path, csrf_token=token)
        confirmation = kitty_parser.parse_guest_confirmation(
            response.text, f"/{self.kitty_id}{path}"
        )
        if confirmation:
            response = self._request(
                "POST",
                path,
                data={"skip_account_prompt": "true"},
                csrf_token=confirmation,
            )
        location = urlparse(response.url)
        if location.hostname != "www.kittysplit.com" or location.path.rstrip(
            "/"
        ) not in {
            f"/{self.kitty_id}",
            f"/{self.kitty_id}/entries",
        }:
            raise ValueError("Kittysplit did not confirm the selected participant.")

    @kitty_endpoint("/entries/", user_needs_to_be_selected=True)
    def get_expenses(
        self,
        expense_type: kitty_parser.ExpenseType = kitty_parser.ExpenseType.ALL,
        **kwargs,
    ) -> List[dict]:
        response = self._request(kwargs.pop("method"), kwargs.pop("path"))
        expenses = kitty_parser.parse_expenses(
            response.text,
            expense_type=expense_type,
            viewing_party_id=self.selected_viewing_party_id,
        )

        # add base url to detail expense pages
        for expense in expenses:
            detail_url = expense["url"]
            if detail_url.startswith("/"):  # remove leading slash
                detail_url = detail_url[1:]
            expense["url"] = self.base_url + detail_url

        return expenses

    @kitty_endpoint("/entries/{}/edit", user_needs_to_be_selected=True)
    def get_expense(self, entry_id: str, **kwargs) -> dict:
        response = self._request(
            kwargs.pop("method"), fill_query_params(kwargs.pop("path"), entry_id)
        )

        parsed_flat_expense_detail = kitty_parser.parse_expense(response.text)
        return kitty_parser.parse_flat_expense_detail(parsed_flat_expense_detail)

    @kitty_endpoint(
        "/entries/{}/delete",
        method="POST",
        user_needs_to_be_selected=True,
    )
    def delete_expense(self, entry_id: str, **kwargs) -> None:
        action = fill_query_params(kwargs.pop("path"), entry_id)
        token = None
        if self._uses_participant_chooser:
            token = self._get_form_token(
                fill_query_params("/entries/{}", entry_id), action
            )
        self._request(kwargs.pop("method"), action, csrf_token=token)

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
            form_data[f"entry[entry_shares][{idx}][number_of_people_string]"] = (
                "1 person"
            )
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
