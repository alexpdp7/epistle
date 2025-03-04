import argparse
import cmd
import datetime
import pathlib
import re
import subprocess
import tempfile

from epistle import notmuch, terminal


def watch(_args):
    nm = notmuch.Notmuch()

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
        message = self._get_message_from_arg(arg)
        print(message.as_text())
        attachments = message.attachments()
        if attachments:
            print("Attachments:")
            print()
            for attachment in attachments:
                print(
                    f"<{attachment['id']}>",
                    attachment["filename"],
                    attachment["content-length"],
                )

    def do_cat_attachment(self, args):
        message, attachment = args.split()
        message = self._get_message_from_arg(message)
        meta, attachment = message.attachment(attachment)
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = pathlib.Path(tempdir)
            attachment_path = tempdir / "attachment"
            attachment_path.write_bytes(attachment)
            if meta["content-type"] == "application/pdf":
                subprocess.run(
                    ["pdftotext", "-layout", "-nopgbrk", attachment_path, "-"],
                    check=True,
                )
                return
            if meta["filename"].endswith(".docx"):
                subprocess.run(
                    ["libreoffice", "--cat", attachment_path],
                    check=True,
                )
                return
            assert False, f"don't know what to do with {meta}"

    def do_archive(self, arg):
        for message in self._get_messages_from_arg(arg):
            message.archive()
        self.do_list(None)

    def do_delete(self, arg):
        for message in self._get_messages_from_arg(arg):
            message.delete()
        self.do_list(None)

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

    def _get_message_from_arg(self, arg):
        assert re.match(r"\d+$", arg), f"{arg} should be a number"
        index = int(arg) - 1
        return self.messages[index]

    def _get_messages_from_arg(self, arg):
        assert re.match(r"^[\d\s]+$", arg), f"{arg} should numbers separated by whitespace"
        return [self.messages[int(m)-1] for m in arg.split()]


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
