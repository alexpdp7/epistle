# epistle

A terminal mail client with the following properties:

* Supports multiple accounts without additional configuration.
* Supports GMail quirks without additional configuration.
* Works on mbsync-synchronized maildirs without additional configuration.
  If you use mbsync to keep a copy of your email, then you can automatically use epistle on top.
  mbsync synchronizes changes you make locally, such as deleting and archiving, upstream to your main mail account.

I develop epistle by implementing features as I need them.
Features are very limited:

* You can read email.
* You can archive email (on Yahoo and GMail) and delete email (on Yahoo).

epistle uses mbsync and [notmuch](https://notmuchmail.org/) to perform the heavy lifting.

## Requirements

You must have `notmuch` configured for emails synchronized with mbsync.

`epistle` expects that the first level of your mail directory corresponds to different email accounts.
That is, with `~/.notmuch-config`:

```
[database]
path=/home/user/Mail
```

, you should have directories like `/home/user/Mail/example@example.com`.

`epistle` watches a file named `.lock` in your mail folder.
Your sync process **MUST** create this file when beginning to sync, and remove the file at the end.

## Implemented features

### Checking for new email

```
epistle watch
```

Prints your unread mail, then waits for new messages.
When new messages arrive, `epistle watch` prints them and quits.
If your terminal notifies you when commands finish, then you receive a new notification when you receive new email.

If you run `epistle watch` over `ssh`, then use `ssh -tt ... epistle watch` to ensure proper behavior.

### Reading mail

```
epistle read
```

* `list` lists emails (currently, only the inbox).
* `read n` or `n` reads the nth message (does not mark as read yet).
* `delete n` or `archive n` delete or archive the nth message (marking as read).
* `quit` quits.

### GMail support

`epistle` is aware of some GMail quirks, like tagged emails being duplicated to the "All Mail" folder.

## Plan

### Nice messages for everyone

Plain text emails are frequently formatted uglily in graphical mail clients.

`epistle` will invoke your editor to compose your emails in plain text, using a Markdown-like syntax.
When sending the email, `epistle` will send a correctly formatted plain text version (wrapped, etc.), and a rendered HTML version with Markdown-like formatting.

This should result in emails perfectly readable on terminal mail clients, and pretty (but minimalistic) emails on graphical clients.
