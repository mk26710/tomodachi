from typing import Tuple

import discord

from tomodachi.core.icons import Icons
from tomodachi.utils import HUMAN_READABLE_FLAGS

__all__ = ["humanize_flags", "avatar_or_default"]


def _humanize_iteration_filter(o: Tuple[str, bool]):
    return o[1]


def humanize_flags(flags: discord.PublicUserFlags):
    for name, value in filter(_humanize_iteration_filter, flags):
        yield f"{Icons()(name)} {HUMAN_READABLE_FLAGS[name]}"


def avatar_or_default(user: discord.User):
    if not user.avatar:
        return user.default_avatar
    return user.avatar
