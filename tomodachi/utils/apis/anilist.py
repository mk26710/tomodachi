#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Optional, TypedDict

from aiohttp import ClientSession

from tomodachi.core.exceptions import AniListException

__all__ = ["AniList", "AniMedia", "MediaType"]


class MediaType(Enum):
    ANIME = "ANIME"
    MANGA = "MANGA"


class MediaTitle(TypedDict):
    romaji: Optional[str]
    english: Optional[str]
    native: Optional[str]


class MediaCoverImage:
    __slots__ = ("extra_large", "large", "medium", "color")

    def __init__(self, **kwargs):
        self.extra_large = kwargs.get("extraLarge")
        self.large = kwargs.get("large")
        self.medium = kwargs.get("medium")
        self.color = kwargs.get("color")


class AniMedia:
    __slots__ = (
        "id",
        "title",
        "_type",
        "_description",
        "genres",
        "duration",
        "_startDate",
        "mean_score",
        "average_score",
        "status",
        "_coverImage",
        "banner_image",
        "url",
        "episodes",
        "_is_adult",
        "volumes",
        "chapters",
    )

    def __init__(self, **kwargs):
        self.id: int = kwargs.get("id")
        self.title: MediaTitle = kwargs.get("title", {})
        self._type: str = kwargs.get("type")
        self._description: str = kwargs.get("description")
        self.genres: list[str] = kwargs.get("genres", [])
        self.duration: int = kwargs.get("duration", 0)
        self._startDate: dict[str, int] = kwargs.get("startDate", {})
        self.mean_score: int = kwargs.get("meanScore", 0)
        self.average_score: Optional[int] = kwargs.get("averageScore", 0)
        self.status: str = kwargs.get("status")
        self._coverImage: dict[str, str] = kwargs.get("coverImage")
        self.banner_image: str = kwargs.get("bannerImage")
        self.url: str = kwargs.get("siteUrl")
        self.episodes: int = kwargs.get("episodes")
        self._is_adult: bool = kwargs.get("isAdult", False)
        self.volumes: Optional[int] = kwargs.get("volumes", 0)
        self.chapters: Optional[int] = kwargs.get("chapters", 0)

    def __repr__(self):
        return f"<AniMedia id={self.id} title={self.title}>"

    @property
    def type(self):
        return MediaType(self._type)

    @property
    def description(self):
        # absolute genius move here
        desc = self._description or ""
        return desc.replace("\n", "").replace("<br>", "\n")

    @property
    def start_date(self):
        if any(n is None for n in self._startDate.values()):
            return None

        return datetime(self._startDate["year"], self._startDate["month"], self._startDate["day"], tzinfo=timezone.utc)

    @property
    def cover_image(self):
        return MediaCoverImage(**self._coverImage)

    @property
    def is_adult(self):
        return self._is_adult


class AniList:
    __base_url: ClassVar[str] = "https://graphql.anilist.co"
    __session: ClassVar[Optional[ClientSession]] = None

    @classmethod
    async def setup(cls, session):
        cls.__session = session

    @classmethod
    async def lookup(cls, search: str, _type: MediaType = MediaType.ANIME, *, raw=False, hide_adult=True):
        query = """
                query ($id: Int, $page: Int, $search: String, $type: MediaType) {
                  Page(page: $page, perPage: 100) {
                    pageInfo {
                      total
                      currentPage
                      lastPage
                      hasNextPage
                      perPage
                    }
                    media(id: $id, search: $search, type: $type, sort: POPULARITY_DESC) {
                      type
                      id
                      title {
                        romaji
                        english
                        native
                      }
                      description
                      genres
                      duration
                      startDate {
                        year
                        month
                        day
                      }
                      meanScore
                      averageScore
                      status
                      coverImage {
                        extraLarge
                        large
                        medium
                        color
                      }
                      bannerImage
                      siteUrl
                      episodes
                      isAdult
                      volumes
                      chapters
                    }
                  }
                }
        """

        variables = {
            "type": _type.name,
            "search": search,
            "page": 1,
        }

        response = await cls.__session.post(cls.__base_url, json={"query": query, "variables": variables})
        _json = await response.json()

        if "errors" in _json.keys():
            raise AniListException(_json)

        if raw:
            return _json

        if hide_adult:
            return [
                AniMedia(**obj)
                for obj in _json["data"]["Page"]["media"]
                if (obj["isAdult"] is False and "Hentai" not in obj["genres"])
            ]
        else:
            return [AniMedia(**obj) for obj in _json["data"]["Page"]["media"]]
