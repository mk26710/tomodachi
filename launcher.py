#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import importlib
import logging
import os.path
import sys
from typing import Any

import discord
from loguru import logger

import config
import patches  # noqa
from intercept_handler import InterceptHandler
from tomodachi.core.bot import Tomodachi
from tomodachi.utils import pg

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

try:
    uvloop: Any = importlib.import_module("uvloop")
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def setup_jishaku():
    # Enforcing jishaku flags
    for flag in config.JISHAKU_FLAGS:
        os.environ[f"JISHAKU_{flag}"] = "True"


def setup_logging():
    # we need to get rid of default handler
    logger.remove()

    stdout_level = os.environ.get("LOGGING_LEVEL", "INFO")
    fmt = "{time} - {name} - {level} - {message}"

    logging.getLogger().setLevel(stdout_level)
    logging.getLogger().handlers = [InterceptHandler()]

    # Root logger
    logger.add(
        sys.stderr,
        colorize=True,
        level=stdout_level,
        enqueue=True,
    )

    # Sink for reminders logs
    logger.level("REMINDERS", no=1, icon="🕐", color="<blue>")

    logger.add(
        os.path.join(ROOT_DIR, "logs", "reminders", "{time}.log"),
        format=fmt,
        rotation="500 MB",
        filter="tomodachi.exts.reminders",
        level="REMINDERS",
        enqueue=True,
    )


setup_logging()
setup_jishaku()

# Creating database pool
loop = asyncio.get_event_loop()
loop.run_until_complete(pg().setup(config.POSTGRES_DSN))

# Running the bot
tomodachi = Tomodachi(ROOT_DIR=ROOT_DIR)
tomodachi.load_extension("jishaku")

try:
    loop.run_until_complete(tomodachi.start(config.TOKEN))

except KeyboardInterrupt:
    loop.run_until_complete(tomodachi.close())

finally:
    discord.client._cleanup_loop(loop)  # noqa
