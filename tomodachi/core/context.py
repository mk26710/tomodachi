#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Optional

from discord.ext import commands

from tomodachi.core.menus import TomodachiMenu

if TYPE_CHECKING:
    from discord import User, Guild, Member, Message

    from tomodachi.core.bot import Tomodachi
    from tomodachi.core.menus import MenuEntries

__all__ = ["TomodachiContext"]


class TomodachiContext(commands.Context):
    bot: Tomodachi
    guild: Optional[Guild]
    author: Union[Member, User]
    command: commands.Command
    message: Message

    def __init__(self, **attrs):
        super().__init__(**attrs)

    @staticmethod
    def new_menu(entries: MenuEntries, *, title: Optional[str] = ""):
        return TomodachiMenu(entries, title=title)

    async def get_settings(self):
        return await self.bot.cache.get_settings(self.guild.id)

    async def refresh_cache(self):
        await self.bot.cache.refresh_settings(self.guild.id)
