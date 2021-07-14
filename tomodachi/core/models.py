#  Copyright (c) 2020 — present, kodamio.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import List, Optional

import attr

__all__ = ["Settings"]


@attr.s(slots=True, auto_attribs=True)
class Settings:
    guild_id: Optional[int] = None
    prefix: Optional[str] = None
    lang: Optional[str] = "en_US"
    mute_role: Optional[int] = None
    mod_roles: Optional[List[int]] = []
    audit_infractions: Optional[bool] = True
    dm_targets: Optional[bool] = False
