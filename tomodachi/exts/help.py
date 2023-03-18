#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Union, Mapping, Optional

import discord
from discord.ext import commands
from more_itertools import chunked

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.core.menus import TomodachiMenu
from tomodachi.utils.icons import i

if TYPE_CHECKING:
    Commands = List[Union[commands.Command, commands.Group]]
    MenuPayload = List[Dict[str, str]]
    MenuEntries = MenuPayload

PREFIX_PLACEHOLDER = re.compile(r"%prefix%", re.MULTILINE)


class BotHelpMenu(TomodachiMenu):
    def __init__(
        self,
        entries: MenuEntries,
        *,
        title: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        inline_fields: bool = True,
        note: Optional[str] = None,
        colour: Optional[Union[discord.Colour, int]] = None,
    ):
        super().__init__(list(chunked(entries, 6)), title=title, embed=embed)
        self.inline_fields = inline_fields
        if note:
            self.embed.description = note
        if colour is not None:
            self.embed.colour = colour

    async def format_embed(self, payload: MenuPayload):
        self.embed.clear_fields()
        if self.max_index > 0:
            self.embed.set_footer(text=f"Page {self.current_index + 1} / {self.max_index + 1}")

        for entry in payload:
            for key, value in entry.items():
                self.embed.add_field(name=key, value=value, inline=self.inline_fields)


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

    async def send_bot_help(self, mapping: Mapping[Optional[CogMixin], List[commands.Command]]):
        mapping = sorted(mapping.items(), key=lambda m: len(m[1]), reverse=True)

        entries = []
        for cog, commands in mapping:
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [f"`{c.qualified_name}`" for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "formatted_name", "No Category")
                entries.append({cog_name: " ".join(command_signatures)})

        menu = BotHelpMenu(entries, title="Available commands", note=self.get_opening_note())
        await menu.start(self.context, channel=self.get_destination())

    def get_command_signature(self, command):
        return f"{command.qualified_name} {command.signature}"

    async def send_cog_help(self, cog: CogMixin):
        channel = self.get_destination()
        filtered: Commands = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            return await channel.send("\N{LOCK} You can't use any commands from this cog.")

        entries = []
        for command in filtered:
            command_name = self.get_command_signature(command)
            entries.append({command_name: command.short_doc or "Missing description."})

        menu = BotHelpMenu(
            entries,
            title=f"{cog.formatted_name}",
            note=cog.description,
            inline_fields=False,
            colour=cog.colour,
        )

        await menu.start(self.context, channel=channel)

    async def send_group_help(self, group):
        channel = self.get_destination()
        filtered: Commands = await self.filter_commands(group.commands, sort=True)
        if not filtered:
            return await channel.send("\N{LOCK} You can't use any commands from this group.")

        entries = []
        for command in filtered:
            command_name = self.get_command_signature(command)
            entries.append({command_name: command.short_doc or "Missing description."})

        menu = BotHelpMenu(
            entries,
            title=f"{group.qualified_name} commands group",
            note=group.description,
            inline_fields=False,
        )

        await menu.start(self.context, channel=channel)

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
