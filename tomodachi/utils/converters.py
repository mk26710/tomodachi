#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from discord.ext.commands import Converter, BadArgument


class uint(Converter, int):  # noqa
    async def convert(self, ctx, argument):
        if not argument.isdigit():
            raise BadArgument(f"{argument} must be an unsigned integer")

        return int(argument)
