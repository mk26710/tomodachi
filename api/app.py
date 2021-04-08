#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import io

from PIL import Image
from gtts import gTTS
from fastapi import Header, Depends, FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.exceptions import HTTPException


class TTSModel(BaseModel):
    language: str
    text: str


async def verify_secret(request: Request, authorization: str = Header(...)):
    """Authorizes requests"""
    if authorization != request.app.state.secret:
        raise HTTPException(status_code=403, detail="Authorization header is invalid")


app = FastAPI(dependencies=[Depends(verify_secret)])


@app.get("/ping")
async def read_root():
    return PlainTextResponse("Pong!")


@app.get("/tts")
def get_tts(tts: TTSModel):
    buff = io.BytesIO()

    try:
        tts = gTTS(text=tts.text, lang=tts.language)
    except ValueError:
        return PlainTextResponse("Make sure the language code is correct.", status_code=400)
    else:
        tts.write_to_fp(buff)
    buff.seek(0)

    return StreamingResponse(buff, media_type="audio/mp3", status_code=200)


@app.get("/square/{r}/{g}/{b}")
def get_square(r: int, g: int, b: int):
    buff = io.BytesIO()
    with Image.new("RGB", (256, 256), (r, g, b)) as im:
        im.save(buff, format="png")
    buff.seek(0)

    return StreamingResponse(buff, media_type="image/png", status_code=200)
