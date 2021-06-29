#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

#  This file is absolute mess, don't read unless you enjoy tormenting yourslef :)

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from datetime import datetime

import attr

from tomodachi.core.enums import ActionType, InfractionType
from tomodachi.core.actions import Action

if TYPE_CHECKING:
    from tomodachi.core.bot import Tomodachi


def convert_inf_type(val: Any):
    if val is None:
        return None
    if isinstance(val, InfractionType):
        return val
    return InfractionType(val)


@attr.s(slots=True, auto_attribs=True)
class Infraction:
    id: Optional[int] = None
    action_id: Optional[int] = None
    inf_type: Optional[InfractionType] = attr.ib(converter=convert_inf_type, default=None)
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    guild_id: Optional[int] = None
    mod_id: Optional[int] = None
    target_id: Optional[int] = None
    reason: Optional[str] = None


class Infractions:
    def __init__(self, bot: Tomodachi) -> None:
        self.bot = bot

    async def get_by_action(self, id: int):
        """Get specific infraction by action ID"""
        async with self.bot.db.pool.acquire() as conn:
            query = "SELECT * FROM infractions WHERE action_id=$1;"
            record = await conn.fetchrow(query, id)

        if not record:
            return None
        return Infraction(**record)

    async def create(
        self,
        infraction: Optional[Infraction] = None,
        *,
        inf_type: Optional[InfractionType] = None,
        expires_at: Optional[datetime] = None,
        guild_id: Optional[int] = None,
        mod_id: Optional[int] = None,
        target_id: Optional[int] = None,
        reason: Optional[str] = None,
        create_action: bool = True,
    ):
        """Creates an infraction and store it in database"""
        # if user doesn't provide an infraction object the function will create it
        infraction = infraction or Infraction(
            inf_type=inf_type,
            expires_at=expires_at,
            guild_id=guild_id,
            mod_id=mod_id,
            target_id=target_id,
            reason=reason,
        )
        # action_type, trigger_at, author_id, guild_id, channel_id, message_id, extra - are required fields
        # but since it's an infraction we can ignore channel and message ids because it is not a reminder
        action = Action(
            action_type=ActionType.INFRACTION,
            trigger_at=infraction.expires_at,
            guild_id=infraction.guild_id,
        )

        if create_action:
            # override prepared action object with the one from db
            action = await self.bot.actions.create_action(action)

        async with self.bot.db.pool.acquire() as conn:
            query = """INSERT INTO infractions
            (action_id, inf_type, created_at, expires_at, guild_id, mod_id, target_id, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *;"""

            record = await conn.fetchrow(
                query,
                action.id,
                getattr(infraction.inf_type, "name", None),
                action.created_at,
                infraction.expires_at,
                infraction.guild_id,
                infraction.mod_id,
                infraction.target_id,
                infraction.reason,
            )

        return Infraction(**record)
