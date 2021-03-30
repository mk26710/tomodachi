#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from datetime import timedelta

from discord.ext.commands import Converter, BadArgument


class uint(Converter, int):  # noqa
    async def convert(self, ctx, argument):
        if not argument.isdigit():
            raise BadArgument(f"{argument} must be an unsigned integer")

        return int(argument)


time_regex = re.compile(r"(\d{1,5})([smhd])")

units_to_seconds = {
    "d": 86400,
    "h": 3600,
    "m": 60,
    "s": 1,
}


class TimeUnit(Converter, timedelta):
    async def convert(self, ctx, argument):
        match = re.match(time_regex, argument)
        if not match:
            raise BadArgument(f'"{argument}" is invalid time input.')

        amount, unit = match.groups()
        seconds = units_to_seconds.get(unit) * int(amount)

        return timedelta(seconds=seconds)


entry_id_regex = re.compile(r"(#?)(\d{1,7})")


class EntryID(Converter, int):
    async def convert(self, ctx, argument):
        match = re.match(entry_id_regex, argument)
        if not match:
            raise BadArgument(f'"{argument}" is invalid entry ID.')

        _, num = match.groups()
        return int(num)
