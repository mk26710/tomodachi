#  Copyright (c) 2020 — present, kodamio.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.


class humanbool:
    def __init__(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("humanbool values can be only booleans.")
        self.value = value

    def __str__(self):
        if self.value is True:
            return "enabled"
        else:
            return "disabled"
