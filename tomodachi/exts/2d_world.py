#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from datetime import datetime

import discord
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiMenu, TomodachiContext
from tomodachi.utils.apis import AniList, AniMedia, MediaType

waifu_categories = (
    "waifu",
    "neko",
    "shinobu",
    "megumin",
    "bully",
    "cuddle",
    "cry",
    "hug",
    "awoo",
    "kiss",
    "lick",
    "pat",
    "smug",
    "bonk",
    "yeet",
    "blush",
    "smile",
    "wave",
    "smile",
    "wave",
    "highfive",
    "handhold",
    "nom",
    "bite",
    "glomp",
    "kill",
    "slap",
    "happy",
    "wink",
    "poke",
    "dance",
    "cringe",
    "blush",
)


class AniListMenu(TomodachiMenu):
    async def format_embed(self, media: AniMedia):
        self.embed.clear_fields()

        media_title = media.title.get("english") or media.title.get("romaji") or media.title.get("native")
        title = f"{media_title} ({self.current_index + 1}/{self.max_index + 1})"

        self.embed.title = title
        self.embed.url = media.url

        if media.cover_image.color:
            self.embed.colour = await commands.ColourConverter().convert(None, media.cover_image.color)
        else:
            self.embed.colour = 0x2F3136

        self.embed.description = media.description
        self.embed.timestamp = media.start_date or discord.Embed.Empty

        self.embed.set_image(url=media.banner_image or media.cover_image.large)

        if media.type is MediaType.ANIME:
            self.embed.add_field(name="Episodes", value=f"`{media.episodes}`")
            self.embed.add_field(name="Average duration", value=f"`{media.duration}` minutes")

        if media.type is MediaType.MANGA:
            self.embed.add_field(name="Volumes", value=f"`{media.volumes}`")
            self.embed.add_field(name="Chapters", value=f"`{media.chapters}`")

        if media.average_score is not None:
            self.embed.add_field(name="Average score", value=f"`{media.average_score}%`")
        else:
            self.embed.add_field(name="Mean score", value=f"`{media.mean_score}`%")

        if media.genres:
            self.embed.add_field(name="Genres", value=", ".join(media.genres))


class TwoDimWorld(CogMixin, name="アニメ", icon="\N{DANGO}", colour=0xFCB1E3):
    """Commands related to the otaku culture.
    Please note that adult content is only available in the NSFW channels."""

    @commands.command(hidden=True)
    async def impulse(self, ctx: TomodachiContext):
        """Hey, that's another easter egg!"""
        await ctx.send("https://youtu.be/hkL4hW4eniI")

    @commands.is_nsfw()
    @commands.cooldown(1, 7.0, commands.BucketType.user)
    @commands.command(help="Finds some waifus for you", description="Technically it should be SFW, but sometimes not")
    async def anipic(self, ctx: TomodachiContext, *, query: str = "waifu"):
        if query.lower() not in waifu_categories:
            raise commands.BadArgument(f"`{query}` is invalid waifu category")

        url = f"https://waifu.pics/api/sfw/{query}"

        async with self.bot.session.get(url) as resp:
            data = await resp.json()

        embed = discord.Embed(timestamp=datetime.utcnow())
        embed.set_image(url=data["url"])

        icon_url = avatar.url if (avatar := ctx.author.avatar) else ctx.author.default_avatar
        embed.set_footer(icon_url=icon_url, text=f"Requested by {ctx.author}")

        await ctx.send(embed=embed)

    @commands.cooldown(1, 7.0, commands.BucketType.user)
    @commands.command(help="Searches for information about mangas on AniList")
    async def manga(self, ctx: TomodachiContext, *, query: str):
        async with ctx.typing():
            data = await AniList.lookup(query, MediaType.MANGA, hide_adult=not ctx.channel.is_nsfw())
            if not data:
                return await ctx.send(embed=discord.Embed(title=":x: Nothing was found!"))

            menu = AniListMenu(data)
            await menu.start(ctx)

    @commands.cooldown(1, 7.0, commands.BucketType.user)
    @commands.command(help="Searches for information about animes on AniList")
    async def anime(self, ctx: TomodachiContext, *, query: str):
        async with ctx.typing():
            data = await AniList.lookup(query, hide_adult=not ctx.channel.is_nsfw())
            if not data:
                return await ctx.send(embed=discord.Embed(title=":x: Nothing was found!"))

            menu = AniListMenu(data)
            await menu.start(ctx)


def setup(bot):
    bot.add_cog(TwoDimWorld(bot))
