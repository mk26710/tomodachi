#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections import defaultdict

import discord

from tomodachi.utils.singleton import MetaSingleton

__all__ = ["Icons"]

DEFAULT_EMOJI_FALLBACK = discord.PartialEmoji(name="U00002139")


class Icons(metaclass=MetaSingleton):
    __slots__ = ("_store",)

    def __init__(self):
        self._store = defaultdict(lambda: DEFAULT_EMOJI_FALLBACK)

    def __call__(self, name: str):
        return self._store[name]

    def __getitem__(self, item):
        return self._store[item]

    async def setup(self, emojis: list[discord.Emoji]):
        for e in emojis:
            partial = discord.PartialEmoji(name=e.name, id=e.id)
            self._store[e.name.lower()] = partial
