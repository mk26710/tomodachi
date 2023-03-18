#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  Heavily inspired by https://github.com/Rapptz/RoboDanny <

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Union, Optional, TypedDict, final
from datetime import datetime

import attr
import ujson

from tomodachi.utils import helpers
from tomodachi.core.enums import ActionType

if TYPE_CHECKING:
    from tomodachi.core.bot import Tomodachi

__all__ = ["Action", "ActionScheduler"]


class ReminderExtras(TypedDict):
    content: str


class InfractionExtras(TypedDict):
    target_id: int
    reason: str


def convert_action_type(val: Any) -> ActionType:
    if isinstance(val, ActionType):
        return val
    return ActionType(val)


def convert_extra(val: Any) -> Optional[dict]:
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    return ujson.loads(val)


@attr.s(slots=True, auto_attribs=True)
class Action:
    id: Optional[int] = None
    action_type: Optional[ActionType] = attr.ib(converter=convert_action_type, default=ActionType.REMINDER)
    created_at: Optional[datetime] = attr.ib(factory=helpers.utcnow)
    trigger_at: Optional[datetime] = attr.ib(factory=helpers.utcnow)
    author_id: Optional[int] = None
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    extra: Optional[Union[ReminderExtras, InfractionExtras]] = attr.ib(converter=convert_extra, default=None)


@final
class ActionScheduler:
    def __init__(self, bot: Tomodachi):
        self.bot = bot
        self.cond = asyncio.Condition()
        self.task = asyncio.create_task(self.dispatcher())
        self.active: Optional[Action] = None

    async def dispatcher(self):
        async with self.cond:
            action = self.active = await self.get_action()

            if not action:
                await self.cond.wait()
                await self.redispatch()

            now = helpers.utcnow()
            if action.trigger_at >= now:
                delta = (action.trigger_at - now).total_seconds()
                await asyncio.sleep(delta)

            await self.trigger_action(action)
            await self.redispatch()

    async def redispatch(self):
        if not self.task.cancelled() or self.task.done():
            self.task.cancel()

        self.task = asyncio.create_task(self.dispatcher())

        async with self.cond:
            self.cond.notify_all()

    async def get_action(self):
        async with self.bot.db.pool.acquire() as conn:
            query = """SELECT *
                FROM actions
                WHERE (CURRENT_TIMESTAMP + '28 days'::interval) > actions.trigger_at
                ORDER BY actions.trigger_at
                LIMIT 1;"""
            stmt = await conn.prepare(query)
            record = await stmt.fetchrow()

        if not record:
            return None

        return Action(**record)

    async def schedule(self, a: Action):
        now = helpers.utcnow()
        delta = (a.trigger_at - now).total_seconds()

        if delta <= 60 and a.action_type is not ActionType.INFRACTION:
            asyncio.create_task(self.trigger_short_action(delta, a))
            return a

        async with self.bot.db.pool.acquire() as conn:
            await conn.set_type_codec("jsonb", encoder=ujson.dumps, decoder=ujson.loads, schema="pg_catalog")

            query = """INSERT INTO actions (action_type, trigger_at, author_id, guild_id, channel_id, message_id, extra)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *;"""
            stmt = await conn.prepare(query)
            record = await stmt.fetchrow(
                a.action_type.name,
                a.trigger_at,
                a.author_id,
                a.guild_id,
                a.channel_id,
                a.message_id,
                a.extra,
            )

        a = Action(**record)
        # Once the new action created dispatcher has to be restarted
        # but only if the currently active action happens later than new
        if (self.active and self.active.trigger_at >= a.trigger_at) or self.active is None:
            asyncio.create_task(self.redispatch())

        return a

    async def trigger_action(self, action: Action):
        if action.action_type is ActionType.INFRACTION:
            infraction = await self.bot.infractions.get_by_action(action.id)
            self.bot.dispatch("expired_infraction", infraction=infraction)

        else:
            self.bot.dispatch("triggered_action", action=action)

        await self.bot.db.pool.execute("DELETE FROM actions WHERE id = $1;", action.id)

    async def trigger_short_action(self, seconds, action: Action):
        await asyncio.sleep(seconds)
        self.bot.dispatch("triggered_action", action=action)
