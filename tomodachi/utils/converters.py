#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from datetime import timedelta

import discord
from discord.ext import commands


class BannedUser(commands.Converter, discord.User):
    async def convert(self, ctx, argument: str):
        user = await commands.UserConverter().convert(ctx, argument)
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            raise commands.BadArgument(f":x: {user} is not banned.")
        return user


class uint(commands.Converter, int):  # noqa
    async def convert(self, ctx, argument):
        if not argument.isdigit():
            raise commands.BadArgument(f"{argument} must be an unsigned integer")

        return int(argument)


time_regex = re.compile(r"(\d{1,5})([smhd])")

units_to_seconds = {
    "d": 86400,
    "h": 3600,
    "m": 60,
    "s": 1,
}


class TimeUnit(commands.Converter, timedelta):
    async def convert(self, ctx, argument):
        matches = re.findall(time_regex, argument)
        if not matches:
            raise commands.BadArgument(f'"{argument}" is invalid time input.')

        seconds = sum(units_to_seconds.get(unit) * int(amount) for amount, unit in matches)

        return timedelta(seconds=seconds)


entry_id_regex = re.compile(r"(#?)(\d{1,7})")


class EntryID(commands.Converter, int):
    async def convert(self, ctx, argument):
        match = re.match(entry_id_regex, argument)
        if not match:
            raise commands.BadArgument(f'"{argument}" is invalid entry ID.')

        _, num = match.groups()
        return int(num)
