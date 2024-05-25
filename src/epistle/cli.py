import argparse
import datetime
import re

from epistle import notmuch


def watch(args):
    nm = notmuch.Notmuch()
    if nm.locked:
        print("notmuch locked, waiting...")
        nm.wait_for_lock_state(False)
        print("\a")

    unread_messages = nm.unread_messages()

    seen_ids = set()

    for message in sorted(unread_messages, key=lambda m: m.timestamp):
        if not message.in_trash:
            print(message.line)
            seen_ids.add(message.id)

    new_messages = []

    print()

    while not new_messages:
        print(f"\r{datetime.datetime.now()} Waiting for sync to start ", end="")
        nm.wait_for_lock_state(True)
        print(f"\r{datetime.datetime.now()} Waiting for sync to finish", end="")
        nm.wait_for_lock_state(False)
        print(f"\r{datetime.datetime.now()} ...checking               ", end="")

        new_messages = [message for message in nm.unread_messages() if message.id not in seen_ids and not message.in_trash]

    print("\a")
    for message in new_messages:
        print(message.line)


def read(args):
    nm = notmuch.Notmuch()
    query = nm.inboxes_query()
    messages = list(nm.get_messages(query, True))
    for i, message in enumerate(messages):
        print(i+1, message.line)

    command = input("> ")

    if re.match(r"\d+$", command):
        index = int(command) - 1
        message = messages[index]
        print(message.as_text())

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
