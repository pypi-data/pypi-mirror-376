# sleamdge

A
[feature-rich](https://slidge.im/docs/sleamdge/main/user/features.html)
[Steam](https://steamcommunity.com/) to
[XMPP](https://xmpp.org/) puppeteering
[gateway](https://xmpp.org/extensions/xep-0100.html), based on
[slidge](https://slidge.im) and
[steamio](https://steam-py.github.io/docs/latest/).

[![CI pipeline status](https://ci.codeberg.org/api/badges/14070/status.svg)](https://ci.codeberg.org/repos/14070)
[![Chat](https://conference.nicoco.fr:5281/muc_badge/slidge@conference.nicoco.fr)](https://slidge.im/xmpp-web/#/guest?join=slidge@conference.nicoco.fr)
[![PyPI package version](https://badge.fury.io/py/sleamdge.svg)](https://pypi.org/project/sleamdge/)




sleamdge lets you chat with users of Steam without leaving your favorite XMPP client.

## Quickstart

```sh
docker run codeberg.org/slidge/sleamdge \  # works with podman too
    --jid steam.example.org \  # can be whatever you want it to be
    --secret some-secret \  # must match your XMPP server config
    --home-dir /somewhere/writeable  # for data persistence
```

Use the `:latest` tag for the latest release, `:vX.X.X` for release X.X.X, and `:main`
for the bleeding edge.

If you do not like containers, other installation methods are detailed
[in the docs](https://slidge.im/docs/sleamdge/main/admin/install.html).

## Documentation

Hosted on [codeberg pages](https://slidge.im/docs/sleamdge/main/).

## Contributing

Contributions are **very** welcome, and we tried our best to make it easy
to start hacking on sleamdge. See [CONTRIBUTING.md](./CONTRIBUTING.md).
