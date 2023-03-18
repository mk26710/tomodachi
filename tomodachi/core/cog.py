#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Union, Optional

import discord
from discord.ext import commands


if TYPE_CHECKING:
    from tomodachi.core.bot import Tomodachi


__all__ = ["CogMixin"]


class CogMixin(commands.Cog, metaclass=commands.CogMeta):
    def __init_subclass__(cls, *, icon=None, colour=None) -> None:
        cls.icon: Optional[Union[discord.PartialEmoji, str]] = icon
        cls.colour: Optional[Union[discord.Colour, int]] = colour
        cls.color = cls.colour

    def __init__(self, /, tomodachi):
        self.bot: Tomodachi = tomodachi

    @functools.cached_property
    def formatted_name(self):
        if self.icon is not None:
            return f"{self.icon} {self.qualified_name}"
        return self.qualified_name
