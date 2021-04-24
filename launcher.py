#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import logging
import os.path

import aiohttp

import config
import patches  # noqa
from tomodachi.core.bot import Tomodachi
from tomodachi.utils.database import db

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


async def setup_jishaku():
    # Enforcing jishaku flags
    for flag in config.JISHAKU_FLAGS:
        os.environ[f"JISHAKU_{flag}"] = "True"


async def setup_logging():
    # we need to get rid of default handler
    logging.basicConfig(level=logging.INFO)


async def main():
    # Setup all the things
    await setup_logging()
    await setup_jishaku()

    # Create pool connection
    await db.connect()

    # Create new session and start the bot
    async with aiohttp.ClientSession() as session:
        tomodachi = Tomodachi(ROOT_DIR=ROOT_DIR, extra_session=session)
        tomodachi.load_extension("jishaku")

        try:
            await tomodachi.start(config.TOKEN)
        finally:
            await tomodachi.close()


try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()

asyncio.run(main())
