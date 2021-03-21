#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from discord.ext import commands

if TYPE_CHECKING:
    from discord import Guild, Member, User, Message
    from tomodachi.core.bot import Tomodachi

__all__ = ["TomodachiContext"]


class TomodachiContext(commands.Context):
    bot: Tomodachi
    guild: Optional[Guild]
    author: Union[Member, User]
    command: commands.Command
    message: Message

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.icon = self.bot.icon
