import builtins
from collections import abc
import datetime
import itertools
import json
import pathlib
import subprocess
import time


class Notmuch:
    def __init__(self):
        self.database_path = pathlib.Path(
            subprocess.run(
                ["notmuch", "config", "get", "database.path"],
                check=True,
                stdout=subprocess.PIPE,
                encoding="utf8",
            ).stdout.strip()
        )

    @property
    def locked(self):
        return (self.database_path / ".lock").exists()

    @property
    def accounts(self):
        accounts = set()
        for p in self.database_path.iterdir():
            candidate = p.parts[-1]
            if "@" in candidate:
                accounts.add(candidate)
        return accounts

    def wait_for_lock_state(self, state):
        while self.locked != state:
            time.sleep(10)

    def inboxes_query(self):
        return " or ".join(map(get_inbox_query, self.accounts))

    def unread_messages(self):
        return self.get_messages("tag:unread", False)

    def get_messages(self, query, entire_thread):
        return map(
            self.message,
            get_dicts(
                json.loads(
                    subprocess.run(
                        [
                            "notmuch",
                            "show",
                            "--format=json",
                            f"--entire-thread={str(entire_thread).lower()}",
                            "--body=true",
                            "--include-html",
                            query,
                        ],
                        check=True,
                        stdout=subprocess.PIPE,
                        encoding="utf8",
                    ).stdout
                )
            ),
        )

    def message(self, d):
        return NotmuchMessage(self, d)


class NotmuchMessage:
    def __init__(self, notmuch, d):
        self.notmuch = notmuch
        self.d = d

    @property
    def subject(self):
        return self.d["headers"]["Subject"]

    @property
    def id(self):
        return self.d["id"]

    @property
    def _filenames(self) -> abc.Iterator[pathlib.Path]:
        return map(pathlib.Path, self.d["filename"])

    @property
    def _relative_filenames(self) -> abc.Iterable[pathlib.Path]:
        return [f.relative_to(self.notmuch.database_path) for f in self._filenames]

    @property
    def account(self) -> str:
        accounts = set([f.parts[0] for f in self._relative_filenames])
        assert len(accounts) == 1, f"multiple accounts {accounts}"
        return accounts.pop()

    @property
    def line(self):
        folders = ", ".join(["/".join(f) for f in self.friendly_folders])
        return (
            f"{self.timestamp} >{self.account} {folders} <{self.from_} {self.subject}"
        )

    @property
    def is_gmail(self):
        return is_gmail(self.account)

    @property
    def is_yahoo(self):
        return is_yahoo(self.account)

    @property
    def folders(self):
        return set([f.parts[1:-2] for f in self._relative_filenames])

    @property
    def friendly_folders(self):
        if self.is_gmail:
            folders = self.folders
            if len(self.folders) > 1:
                folders.remove(("[Gmail]", "All Mail"))
            return folders
        return self.folders

    @property
    def in_trash(self):
        folders = self.folders
        if self.is_gmail:
            is_trash = ("[Gmail]", "Trash") in folders
            assert not (
                is_trash and len(folders) > 1
            ), f"message in trash and other folders: {folders}"
            return is_trash
        if self.is_yahoo:
            is_trash = ("Trash",) in folders
            assert not (
                is_trash and len(folders) > 1
            ), f"message in trash and other folders: {folders}"
            return is_trash
        assert False, f"unknown account type {self.account}"

    @property
    def timestamp(self):
        return datetime.datetime.fromtimestamp(int(self.d["timestamp"]))

    @property
    def from_(self):
        return self.d["headers"]["From"]

    def as_text(self):
        text = ""
        for header, value in self.d["headers"].items():
            text += f"{header}: {value}\n"
        return text


def get_dicts(x):
    if x is None:
        return []
    match type(x):
        case builtins.dict:
            return [x]
        case builtins.list:
            return list(itertools.chain(*[get_dicts(y) for y in x]))
        case _:
            assert True, f"unexpected {type(x)}"


def is_gmail(account):
    return account.endswith("@gmail.com")


def is_yahoo(account):
    return "@yahoo" in account


def get_inbox_query(account):
    if is_gmail(account):
        inbox_name = "INBOX"
    elif is_yahoo(account):
        inbox_name = "Inbox"
    else:
        assert False, f"unknown account type {account}"

    return f"path:{account}/{inbox_name}/**"
