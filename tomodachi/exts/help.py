#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import re
import itertools
from typing import List, Union

import discord
from discord.ext import commands
from more_itertools import chunked

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.core.menus import TomodachiMenu
from tomodachi.utils.icons import i

# Type alias for a commands mapping, quite helpful
Commands = List[Union[commands.Command, commands.Group]]

PREFIX_PLACEHOLDER = re.compile(r"%prefix%", re.MULTILINE)


class BotHelpMenu(TomodachiMenu):
    def __init__(self, entries, *, note: str, title: str, thumbnail: str = None):
        super().__init__(entries, title=title)
        self.note = note
        self.entries = entries
        self.embed.description = note
        self.embed.colour = 0x2F3136
        self.embed.set_thumbnail(url=thumbnail)

    async def format_embed(self, payload: list[dict[str, list[Union[commands.Command, commands.Group]]]]):
        self.embed.clear_fields()
        if self.max_index > 0:
            self.embed.set_footer(text=f"Page {self.current_index + 1} / {self.max_index + 1}")
        for group in payload:
            for category, _commands in group.items():
                self.embed.add_field(name=category, value=" ".join(f"`{c.qualified_name}`" for c in _commands))


class TomodachiHelpCommand(commands.MinimalHelpCommand):
    context: TomodachiContext

    def __init__(self, **options):
        super().__init__(**options, command_attrs=dict(hidden=True))
        self._e_colour = 0x2F3136

    async def send_pages(self):
        e = discord.Embed(colour=self._e_colour)
        e.description = "".join(self.paginator.pages)

        await self.get_destination().send(embed=e)

    def format_command(self, command: Union[commands.Command, commands.Group]):
        fmt = "`{0}{1}` — {2}\n" if command.short_doc else "`{0}{1}`\n"
        return fmt.format(self.context.prefix, command.qualified_name, command.short_doc)

    async def send_bot_help(self, _):
        def get_category(command):
            _cog: CogMixin = command.cog
            return _cog.formatted_name if _cog is not None else "Uncategorized"

        filtered: Commands = await self.filter_commands(self.context.bot.commands, sort=True, key=get_category)

        grouped = itertools.groupby(filtered, key=get_category)
        iterated = tuple((cat, tuple(cmds)) for cat, cmds in grouped)
        ordered = sorted(iterated, key=lambda x: len("".join(cmd.name for cmd in x[1])), reverse=True)
        chunks = list(chunked(list({cat: list(cmds)} for cat, cmds in ordered), 6))

        menu = BotHelpMenu(
            chunks,
            note=self.get_opening_note(),
            title="Available Commands",
            thumbnail=self.context.bot.user.avatar.url,
        )

        await menu.start(self.context, channel=self.get_destination())

    async def send_cog_help(self, cog: CogMixin):
        description = ""

        embed = discord.Embed(title=cog.formatted_name, colour=self._e_colour)
        embed.set_thumbnail(url=self.context.bot.user.avatar.url)

        if cog.description:
            description += f"{cog.description}\n\n"

        filtered: Commands = await self.filter_commands(cog.get_commands(), sort=True)

        if filtered:
            for command in filtered:
                description += self.format_command(command)

        embed.description = re.sub(PREFIX_PLACEHOLDER, self.context.prefix, description)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        description = ""

        embed = discord.Embed(colour=self._e_colour, title=f"{group} commands")
        embed.set_thumbnail(url=self.context.bot.user.avatar.url)

        filtered: Commands = await self.filter_commands(group.commands, sort=True)
        if filtered:
            for command in filtered:
                description += self.format_command(command)

        embed.description = re.sub(PREFIX_PLACEHOLDER, self.context.prefix, description)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            colour=self._e_colour,
            title=self.get_command_signature(command),
        )

        description = ""
        if command.help:
            description += f"{i:rich_presence} {command.help}"

        if command.description:
            description += f"\n\n{command.description}"

        if description:
            embed.description = re.sub(PREFIX_PLACEHOLDER, self.context.prefix, description)

        if cooldown := command._buckets._cooldown:  # noqa
            embed.add_field(name="Cooldown", value=f"{i:slowmode} {int(cooldown.per)} seconds")

        if command.aliases:
            aliases = (f"`{alias}`" for alias in command.aliases)
            embed.add_field(name="Aliases", value=" ".join(aliases))

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(colour=self._e_colour)
        embed.title = f"{i:question} {error}"

        await self.get_destination().send(embed=embed)


class TomodachiHelp(CogMixin):
    def __init__(self, /, tomodachi):
        super().__init__(tomodachi)
        self._original_help_command = tomodachi.help_command
        tomodachi.help_command = TomodachiHelpCommand()
        tomodachi.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(TomodachiHelp(bot))
