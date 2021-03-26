#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
import ujson


class EmbedOverridden(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.colour = 0x2F3136


discord.Embed = EmbedOverridden


def to_json(obj):
    return ujson.dumps(obj, ensure_ascii=True)


discord.utils.to_json = to_json
