#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio

import uvicorn

import config
from api.app import app

try:
    import uvloop  # noqa
except (ImportError, ModuleNotFoundError):
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

app.state.secret = config.BACKEND_TOKEN

uvicorn.run(app)
