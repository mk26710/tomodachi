#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys
import traceback

import discord
from discord.ext import flags, commands

from tomodachi.core import CogMixin, TomodachiContext


class ErrorHandler(CogMixin):
    def __init__(self, /, tomodachi):
        super().__init__(tomodachi)
        self.ignored = (commands.CommandNotFound,)
        # these error types will remain unhandled
        # but also there will be logging with traceback
        self.suppressed_tracebacks = (
            commands.CheckFailure,
            commands.CheckAnyFailure,
            commands.UserNotFound,
            commands.MemberNotFound,
            commands.BadArgument,
            commands.MissingRequiredArgument,
            commands.MaxConcurrencyReached,
            flags.ArgumentParsingError,
            flags.DontExitArgumentParser,
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: TomodachiContext, error: commands.CommandError):
        error = getattr(error, "original", error)

        # ignored error types are being suppressed
        # along with local error handler in order
        # to let local's handle the error
        if isinstance(error, self.ignored) or hasattr(ctx.command, "on_error"):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id == self.bot.owner_id:
                await ctx.reinvoke()
                return

            retry_after = f"{error.retry_after:.2f}"
            return await ctx.reply(
                f"Please, try again in `{retry_after}` seconds.",
                mention_author=False,
            )

        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.channel.send(f"{error}")

        if not isinstance(error, self.suppressed_tracebacks):
            # send some debug information to bot owner
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

            e = discord.Embed(color=0xFF0000, title="Exception")
            e.add_field(name="Command", value=f"{ctx.message.content[0:1000]}")
            e.add_field(name="Author", value=f"{ctx.author} (`{ctx.author.id}`)")
            e.add_field(name="Guild", value="{}".format(f"{g.name} (`{g.id}`)" if (g := ctx.guild) else "None"))

            if log_c := self.bot.traceback_log:
                await log_c.send(embed=e, content=f"```\n{tb[0:2000]}\n```")


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
