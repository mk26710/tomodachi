#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord

__all__ = ["make_intents", "make_cache_policy"]


def make_intents():
    return discord.Intents(
        members=True,
        presences=True,
        guilds=True,
        emojis=True,
        reactions=True,
        bans=True,
        invites=True,
        messages=True,
    )


def make_cache_policy():
    return discord.MemberCacheFlags(
        joined=True,
        online=True,
        voice=False,
    )
