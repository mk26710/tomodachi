#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections import defaultdict

import discord

__all__ = ["make_progress_bar", "HUMAN_READABLE_FLAGS", "HUMANIZED_ACTIVITY"]


_HUMAN_READABLE_FLAGS = {
    "staff": "Discord Staff",
    "partner": "Discord Partner",
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

HUMANIZED_ACTIVITY = {
    discord.ActivityType.unknown: "Unknown activity",
    discord.ActivityType.playing: "Playing",
    discord.ActivityType.streaming: "Live on Twitch",
    discord.ActivityType.listening: "Listening",
    discord.ActivityType.watching: "Watching",
    discord.ActivityType.custom: "Custom status",
}


def make_progress_bar(position: float, total: float, *, length: int = 15, filler="█", emptiness=" ", in_brackets=False):
    bar = ""

    target_pos = (position * 100) / total

    for i in range(1, length + 1):
        i_pos = round(i * 100 / length)
        bar += filler if i_pos <= target_pos else emptiness
    return bar if not in_brackets else f"[{bar}]"
