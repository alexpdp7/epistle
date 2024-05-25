import builtins
from collections import abc
import datetime
import itertools
import json
import pathlib
import subprocess


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

    def unread_messages(self, *args):
        return map(
            self.message,
            get_dicts(
                json.loads(
                    subprocess.run(
                        [
                            "notmuch",
                            "show",
                            "--format=json",
                            "--entire-thread=false",
                            "tag:unread",
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
        return self.account.endswith("@gmail.com")

    @property
    def is_yahoo(self):
        return "@yahoo" in self.account

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
