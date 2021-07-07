#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import logging
import os.path

import ujson
import aiohttp
import discord

import config
from tomodachi.core.bot import Tomodachi

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


async def setup_jishaku():
    # Enforcing jishaku flags
    for flag in config.JISHAKU_FLAGS:
        os.environ[f"JISHAKU_{flag}"] = "True"


async def setup_logging():
    logging.basicConfig(level=logging.INFO)


async def main():
    # Setup all the things
    await setup_logging()
    await setup_jishaku()

    # Connect to database
    await Tomodachi.db.connect()
    await Tomodachi.db.connection_created.wait()

    # Create new session and start the bot
    session = aiohttp.ClientSession()
    tomodachi = Tomodachi(session=session, root_dir=ROOT_DIR)
    tomodachi.load_extension("jishaku")

    try:
        await tomodachi.start(config.TOKEN)
    finally:
        await tomodachi.close()


# patch d.py with ujson
def to_json(obj):
    return ujson.dumps(obj, ensure_ascii=True)


discord.utils.to_json = to_json

try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()

asyncio.run(main())
