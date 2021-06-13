#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import abc
import functools
from typing import TYPE_CHECKING, Optional

from discord.ext import commands
from discord.partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from tomodachi.core.bot import Tomodachi


__all__ = ["CogMixin", "CogABCMeta"]


class CogABCMeta(commands.CogMeta, abc.ABCMeta):
    def __new__(mcs, *args, **kwargs):
        try:
            icon = kwargs.pop("icon")
        except KeyError:
            icon = None
        new_mcs = super().__new__(mcs, *args, **kwargs)
        new_mcs.icon = icon
        return new_mcs


class Mixin(metaclass=abc.ABCMeta):
    pass


class CogMixin(Mixin, commands.Cog, metaclass=CogABCMeta):
    icon: Optional[PartialEmoji]

    def __init__(self, /, tomodachi):
        self.bot: Tomodachi = tomodachi

    @functools.cached_property
    def formatted_name(self):
        if self.icon is not None:
            return f"{self.icon} {self.qualified_name}"
        return self.qualified_name
