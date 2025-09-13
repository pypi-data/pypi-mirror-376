# matteridge

A
[feature-rich](https://slidge.im/docs/matteridge/main/user/features.html)
[Mattermost](https://mattermost.com) to
[XMPP](https://xmpp.org/) puppeteering
[gateway](https://xmpp.org/extensions/xep-0100.html), based on
[slidge](https://slidge.im) and
[mattermost-api-reference-client](https://git.sr.ht/~nicoco/mattermost-api-reference-client).

[![CI pipeline status](https://ci.codeberg.org/api/badges/14070/status.svg)](https://ci.codeberg.org/repos/14070)
[![Chat](https://conference.nicoco.fr:5281/muc_badge/slidge@conference.nicoco.fr)](https://slidge.im/xmpp-web/#/guest?join=slidge@conference.nicoco.fr)
[![PyPI package version](https://badge.fury.io/py/matteridge.svg)](https://pypi.org/project/matteridge/)




matteridge lets you chat with users of Mattermost without leaving your favorite XMPP client.

## Quickstart

```sh
docker run codeberg.org/slidge/matteridge \  # works with podman too
    --jid mattermost.example.org \  # can be whatever you want it to be
    --secret some-secret \  # must match your XMPP server config
    --home-dir /somewhere/writeable  # for data persistence
```

Use the `:latest` tag for the latest release, `:vX.X.X` for release X.X.X, and `:main`
for the bleeding edge.

If you do not like containers, other installation methods are detailed
[in the docs](https://slidge.im/docs/matteridge/main/admin/install.html).

## Documentation

Hosted on [codeberg pages](https://slidge.im/docs/matteridge/main/).

## Contributing

Contributions are **very** welcome, and we tried our best to make it easy
to start hacking on matteridge. See [CONTRIBUTING.md](./CONTRIBUTING.md).
