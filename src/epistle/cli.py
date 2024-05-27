import argparse
import cmd
import datetime
import re

from epistle import notmuch, terminal


def watch(_args):
    nm = notmuch.Notmuch()
    if nm.locked:
        print("notmuch locked, waiting...")
        nm.wait_for_lock_state(state=False)
        print("\a")

    unread_messages = nm.unread_messages()

    seen_ids = set()

    for message in sorted(unread_messages, key=lambda m: m.timestamp):
        if not message.in_trash:
            print(message.line[0 : terminal.get_columns()])
            seen_ids.add(message.id)

    new_messages = []

    print()

    while not new_messages:
        print(f"\r{datetime.datetime.now()} Waiting for sync to start ", end="")
        nm.wait_for_lock_state(state=True)
        print(f"\r{datetime.datetime.now()} Waiting for sync to finish", end="")
        nm.wait_for_lock_state(state=False)
        print(f"\r{datetime.datetime.now()} ...checking               ", end="")

        new_messages = [
            message
            for message in nm.unread_messages()
            if message.id not in seen_ids and not message.in_trash
        ]

    print("\a")
    for message in new_messages:
        print(message.line)


class Cmd(cmd.Cmd):
    prompt = "(epistle) "

    def __init__(self, *args, **kwargs):
        self.nm = notmuch.Notmuch()
        self.do_inbox(None)
        self.do_list(None)
        super().__init__(*args, **kwargs)

    def do_list(self, _arg):
        self.messages = sorted(
            self.nm.get_messages(self.query, entire_thread=True),
            key=lambda m: m.timestamp,
        )
        for i, message in enumerate(self.messages):
            print(f"{i + 1} {message.line}"[0 : terminal.get_columns()])

    def do_read(self, arg):
        assert re.match(r"\d+$", arg), f"{arg} should be a number"
        index = int(arg) - 1
        message = self.messages[index]
        print(message.as_text())

    def do_quit(self, _arg):
        return True

    def do_inbox(self, _arg):
        self.query = self.nm.inboxes_query()

    def do_EOF(self, arg):  # noqa: N802
        print()
        return self.do_quit(arg)

    def default(self, line):
        if re.match(r"\d+$", line):
            self.do_read(line)
            return
        assert False, f"Unknown command {line}"


def read(_args):
    Cmd().cmdloop()


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    subparser = subparsers.add_parser("watch")
    subparser.set_defaults(func=watch)

    subparser = subparsers.add_parser("read")
    subparser.set_defaults(func=read)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
