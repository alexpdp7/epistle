import argparse
import time

from epistle import notmuch


def watch(args):
    nm = notmuch.Notmuch()
    unread_messages = nm.unread_messages()

    seen_ids = set()

    for message in sorted(unread_messages, key=lambda m: m.timestamp):
        if not message.in_trash:
            print(message.line)
            seen_ids.add(message.id)

    new_messages = False

    print()
    print("Waiting for new messages...")
    print()

    while not new_messages:
        unread_messages = nm.unread_messages()
        for message in unread_messages:
            if message.id not in seen_ids and not message.in_trash:
                print(message.line)
                new_messages = True
        if not new_messages:
           time.sleep(10)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    subparser = subparsers.add_parser("watch")
    subparser.set_defaults(func=watch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
