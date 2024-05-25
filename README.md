# epistle

My [notmuch](https://notmuchmail.org/) frontend.

## Requires

You must have `notmuch` configured for emails in maildir format.

`epistle` expects that the first level of your mail directory corresponds to different email accounts.
That is, with `~/.notmuch-config`:

```
[database]
path=/home/user/Mail
```

, you should have directories like `/home/user/Mail/example@example.com`.

## Implemented features

### Checking for new email

```
epistle watch
```

Prints your unread mail, then waits for new messages.
When new messages arrive, `epistle watch` prints them and quits.
If your terminal notifies you when commands finish, then you receive a new notification when you receive new email.

If you run `epistle watch` over `ssh`, then use `ssh -tt ... epistle watch` to ensure proper behavior.

### GMail support

`epistle` is aware of some GMail quirks, like tagged emails being duplicated to the "All Mail" folder.

## Plan

### Nice messages for everyone

Plain text emails are frequently formatted uglily in graphical mail clients.

`epistle` will invoke your editor to compose your emails in plain text, using a Markdown-like syntax.
When sending the email, `epistle` will send a correctly formatted plain text version (wrapped, etc.), and a rendered HTML version with Markdown-like formatting.

This should result in emails perfectly readable on terminal mail clients, and pretty (but minimalistic) emails on graphical clients.
