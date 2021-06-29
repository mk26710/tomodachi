#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Tuple
from datetime import datetime, timezone
from collections import defaultdict

import discord

from tomodachi.utils.icons import i

__all__ = ["humanize_flags", "avatar_or_default", "make_intents", "make_progress_bar", "humanize_activity", "utcnow"]


def utcnow():
    return datetime.now(timezone.utc)


_HUMAN_READABLE_FLAGS = {
    "staff": "Discord Staff",
    "partner": "Partnered Server Owner",
    "discord_certified_moderator": "Discord Certified Moderator",
    "hypesquad": "HypeSquad Events",
    "bug_hunter": "Discord Bug Hunter",
    "bug_hunter_level_2": "Discord Bug Hunter",
    "hypesquad_balance": "HypeSquad Balance",
    "hypesquad_brilliance": "HypeSquad Brilliance",
    "hypesquad_bravery": "HypeSquad Bravery",
    "early_supporter": "Early Supporter",
    "verified_bot": "Verified Bot",
    "verified_bot_developer": "Verified Bot Developer",
}


def _human_readable_flags_factory():
    return "Unknown flag"


HUMAN_READABLE_FLAGS = defaultdict(_human_readable_flags_factory, _HUMAN_READABLE_FLAGS)


def _humanize_iteration_filter(o: Tuple[str, bool]):
    return o[1]


def humanize_flags(flags: discord.PublicUserFlags):
    for name, value in filter(_humanize_iteration_filter, flags):
        yield f"{i(name)} {HUMAN_READABLE_FLAGS[name]}"


HUMANIZED_ACTIVITY = {
    discord.ActivityType.unknown: "Unknown activity",
    discord.ActivityType.playing: "Playing",
    discord.ActivityType.streaming: "Live on Twitch",
    discord.ActivityType.listening: "Listening",
    discord.ActivityType.watching: "Watching",
    discord.ActivityType.custom: "Custom status",
}


def humanize_activity(activity_type: discord.ActivityType):
    return HUMANIZED_ACTIVITY.get(activity_type)


def avatar_or_default(user: discord.User):
    if not user.avatar:
        return user.default_avatar
    return user.avatar


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


def make_progress_bar(position: float, total: float, *, length: int = 15, filler="█", emptiness=" ", in_brackets=False):
    target_pos = (position * 100) / total
    bar = "".join(filler if round(i * 100 / length) <= target_pos else emptiness for i in range(1, length + 1))
    return bar if not in_brackets else f"[{bar}]"
