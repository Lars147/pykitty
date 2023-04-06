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
