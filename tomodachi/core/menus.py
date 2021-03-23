#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
from typing import Any, Union, final, Optional

import discord
from discord.ext import menus, commands

from tomodachi.core.context import TomodachiContext

__all__ = ["TomodachiMenu"]

Context = Union[TomodachiContext, commands.Context]
MenuEntries = Union[list[Any], tuple[Any], set[Any]]


class IndexNotChanged(Exception):
    pass


class TomodachiMenu(menus.Menu):
    def __init__(self, entries: MenuEntries, *, title: Optional[str] = None):
        super().__init__(timeout=50.0, delete_message_after=False, clear_reactions_after=True)
        self.embed = discord.Embed(title=title)
        self.entries = entries
        self.__current_index = 0
        self.__max_index = len(entries) - 1

    @final
    async def increase_index(self):
        next_index = self.__current_index + 1
        self.__current_index = 0 if next_index > self.__max_index else next_index

    @final
    async def decrease_index(self):
        next_index = self.__current_index - 1
        self.__current_index = self.__max_index if next_index < 0 else next_index

    @final
    async def reset_index(self):
        if self.__current_index == 0:
            raise IndexNotChanged("Current menu page index is already 0")

        self.__current_index = 0

    @final
    async def maximize_index(self):
        if self.__current_index == self.__max_index:
            raise IndexNotChanged("Current menu page index is already maximum value")

        self.__current_index = self.__max_index

    @final
    @property
    def current_index(self):
        return self.__current_index

    @final
    @property
    def max_index(self):
        return self.__max_index

    async def start(self, ctx: Context, *, channel=None, wait=False):
        if len(self.entries) > 1:
            return await super().start(ctx, channel=channel, wait=wait)

        await self.send_initial_message(ctx, ctx.channel)

    async def format_embed(self, payload):
        self.embed.clear_fields()

        self.embed.set_footer(text=f"Page {self.__current_index + 1} / {self.__max_index + 1}")
        self.embed.description = payload

    async def send_initial_message(self, ctx, channel):
        await self.format_embed(self.entries[0])
        return await channel.send(embed=self.embed)

    async def update_page(self):
        await self.format_embed(self.entries[self.__current_index])
        await self.message.edit(embed=self.embed)

    @staticmethod
    async def cleanup(message: discord.Message, seconds: Union[float, int] = 3.0):
        await asyncio.sleep(seconds)
        await message.delete()

    @menus.button("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}")
    async def on_double_arrow_left(self, _payload):
        try:
            await self.reset_index()
        except IndexNotChanged:
            pass
        else:
            await self.update_page()

    @menus.button("\N{BLACK LEFT-POINTING TRIANGLE}")
    async def on_arrow_left(self, _payload):
        await self.decrease_index()
        await self.update_page()

    @menus.button("\N{BLACK RIGHT-POINTING TRIANGLE}")
    async def on_arrow_right(self, _payload):
        await self.increase_index()
        await self.update_page()

    @menus.button("\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}")
    async def on_double_arrow_right(self, _payload):
        try:
            await self.maximize_index()
        except IndexNotChanged:
            pass
        else:
            await self.update_page()

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, _payload):
        self.stop()

    @menus.button("\N{INPUT SYMBOL FOR NUMBERS}")
    async def on_input_number(self, payload: discord.RawReactionActionEvent):
        channel = self.message.channel

        def check(m):
            return m.author.id == payload.user_id and channel.id == m.channel.id

        question = await channel.send(embed=discord.Embed(title="Which page would you like to open?"))

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await question.edit(embed=discord.Embed(title=":x: Too slow! "))
        else:
            if not msg.content.isdigit():
                return await question.edit(embed=discord.Embed(title=":x: You have to provide a digit!"))

            page_to_open = int(msg.content)
            if page_to_open > self.__max_index + 1 or page_to_open < 1:
                return await question.edit(embed=discord.Embed(title=":x: You have to provided an invalid page."))

            if page_to_open == self.__current_index + 1:
                return await question.edit(embed=discord.Embed(title="You are already on this page."))

            await question.edit(embed=discord.Embed(title=f"Opening page {page_to_open}..."))
            self.__current_index = page_to_open - 1
            await self.update_page()

        finally:
            asyncio.create_task(self.cleanup(question))
