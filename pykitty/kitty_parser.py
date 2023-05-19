import re
from html.parser import HTMLParser
from typing import List, Tuple, Union

from bs4 import BeautifulSoup


class CSRFHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.csrf_token: Union[str, None] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag == "input":
            for attr in attrs:
                if attr[0] == "name" and attr[1] == "_csrf_token":
                    for attr2 in attrs:
                        if attr2[0] == "value":
                            self.csrf_token = attr2[1]
                            break
                    break


class KittySplitUserParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.party_ids: List[str] = []
        self.usernames: List[Tuple[str, str]] = []
        self.in_form: bool = False
        self.viewing_party_id: Union[str, None] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag == "form":
            for attr in attrs:
                if attr[0] == "class" and "set-viewing-party" in attr[1]:
                    self.in_form = True
                    break
        elif tag == "input" and self.in_form:
            for attr in attrs:
                if attr[0] == "name" and attr[1] == "viewing_party_id":
                    for attr2 in attrs:
                        if attr2[0] == "value":
                            self.party_ids.append(attr2[1])
        elif tag == "button" and self.in_form:
            self.viewing_party_id = self.party_ids[-1]

    def handle_data(self, data: str) -> None:
        if self.viewing_party_id is not None:
            self.usernames.append((self.viewing_party_id, data.strip()))
            self.viewing_party_id = None
            self.in_form = False


def parse_expense(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", attrs={"class": "edit-entry-form"})

    # Create a dictionary to hold form inputs
    form_data = {}

    # Find all input elements
    inputs = form.find_all("input")

    for input_ in inputs:
        if (
            input_.get("type") == "hidden"
            or input_.get("type") == "text"
            or input_.get("type") == "date"
        ):
            form_data[input_.get("name")] = input_.get("value")

    # Find all select elements
    selects = form.find_all("select")

    for select in selects:
        selected_option = select.find("option", selected=True)
        if selected_option:
            form_data[select.get("name")] = selected_option.get("value")

    return form_data


def set_nested_dict(data, keys, value):
    key = keys.pop(0)

    # if the key is an integer, convert it
    is_int = False
    try:
        idx = int(key)
        is_int = True
    except ValueError:
        pass

    if keys:
        if is_int:
            while len(data) <= idx:
                data.append({})
            set_nested_dict(data[idx], keys, value)
        else:
            if key not in data:
                data[key] = [] if keys[0].isdigit() else {}
            set_nested_dict(data[key], keys, value)
    else:
        if is_int:
            while len(data) <= idx:
                data.append(None)
            data[idx] = value
        else:
            data[key] = value


def parse_key(key):
    pattern = re.compile(r"\[([^\]]+)\]")
    return pattern.findall(key)  # e.g. ['entry', 'entry_shares', '0', 'id']


def parse_flat_expense_detail(parsed_flat_expense: dict) -> dict:
    """Converts a flat expense detail dict to a nested dict.

    For example, the following flat dict:

    data = {
        'entry[entry_type]': 'expense',
        'entry[amount]': '8.95',
        'entry[entry_shares][0][id]': '29717756',
        'entry[entry_shares][0][involved?]': 'false',
        'entry[entry_shares][0][party_id]': '5842874',
        'entry[entry_shares][0][share_str]': '4.475',
        'entry[entry_shares][0][weight]': '0.5',
        'entry[entry_shares][0][number_of_people]': '1.0',
        'entry[entry_shares][0][share_display]': '4.47',
        'entry[entry_shares][0][number_of_people_string]': '1 person',
        'entry[entry_shares][1][id]': '29717755',
        'entry[entry_shares][1][involved?]': 'false',
        'entry[entry_shares][1][party_id]': '5842873',
        'entry[entry_shares][1][share_str]': '4.475',
        'entry[entry_shares][1][weight]': '0.5',
        'entry[entry_shares][1][number_of_people]': '1.0',
        'entry[entry_shares][1][share_display]': '4.47',
        'entry[entry_shares][1][number_of_people_string]': '1 person',
        'entry[description]': 'Aral Station 191147164/Muenchen//DE / Deutsche Kreditbank AG',
        'entry[entry_date_str]': '2023-03-06',
        '_dontcare': 'true',
        'entry[party_id]': '5842873'
    }

    to

    {
        "entry_type": "expense",
        "amount": "8.95",
        "entry_shares": [
            {
                "id": "29717756",
                "involved?": "false",
                "party_id": "5842874",
                "share_str": "4.475",
                "weight": "0.5",
                "number_of_people": "1.0",
                "share_display": "4.47",
                "number_of_people_string": "1 person"
            },
            {
                "id": "29717755",
                "involved?": "false",
                "party_id": "5842873",
                "share_str": "4.475",
                "weight": "0.5",
                "number_of_people": "1.0",
                "share_display": "4.47",
                "number_of_people_string": "1 person"
            }
        ],
        "description": "Aral Station 191147164/Muenchen//DE / Deutsche Kreditbank AG",
        "entry_date_str": "2023-03-06",
        "_dontcare": "true",
        "party_id": "5842873"
    }

    Args:
        parsed_flat_expense (dict): A parsed flat expense detail dict.

    Returns:
        dict: A nested expense detail dict.
    """
    output_dict = {}
    for key, value in parsed_flat_expense.items():
        if key.startswith("entry"):
            keys = parse_key(key)
            set_nested_dict(output_dict, keys, value)
        else:
            output_dict[key] = value
    return output_dict


def parse_expenses(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    for li in soup.find_all(
        "li", class_="entry-list-item list-item entry-all entry-yours"
    ):
        entry = {}
        entry_link = li.find("a", class_="entry-link")
        entry["url"] = entry_link["href"]

        entry_info = entry_link.find("div", class_="col-xs-12").text.strip()
        buyer, amount, description = re.search(
            r"^(.*) (?:paid|hat) €(.*?) (?:for|für) (.*)", entry_info
        ).groups()
        entry["buyer"] = buyer.strip()
        entry["price"] = {"currency": "€", "amount": amount.replace(",", ".").strip()}
        entry["description"] = description.replace(" bezahlt.", "").strip()

        participants_text = entry_link.find(
            "span", class_="entry-label entry-label-parties"
        ).text.strip()
        participants = participants_text.split(": ")[1]
        if participants in ["Alle.", "everyone."]:
            entry["participants"] = "all"
        else:
            entry["participants"] = participants_text.split(": ")[1]

        entries.append(entry)

    return entries
