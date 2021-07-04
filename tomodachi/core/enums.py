#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from enum import Enum

__all__ = ["ActionType", "InfractionType"]


class InfractionType(Enum):
    WARN = "WARN"
    MUTE = "MUTE"
    KICK = "KICK"
    UNBAN = "UNBAN"
    TEMPBAN = "TEMPBAN"
    PERMABAN = "PERMABAN"


class ActionType(Enum):
    REMINDER = "REMINDER"
    INFRACTION = "INFRACTION"
    NOTIFICATION = "NOTIFICATION"
